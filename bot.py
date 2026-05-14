"""
WhatsApp Poll Bot — Core Logic  v1.4
(app_v2 edition: logging goes to stdout so Flask can capture it)
"""
__version__ = "1.4"

import asyncio
import logging
import sys
from pathlib import Path
from typing import Set

from playwright.async_api import (
    BrowserContext,
    Page,
    async_playwright,
    TimeoutError as PWTimeoutError,
)

import config

# ── Logging: force stdout so the Flask subprocess pipe captures everything ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
    force=True,
)
log = logging.getLogger("wa-poll-bot")

# ---------------------------------------------------------------------------
# Selectors
# ---------------------------------------------------------------------------

SEL_QR_SCAN_READY = 'canvas[aria-label="Scan this QR code to link a device"]'
SEL_LOGGED_IN     = '[data-testid="chatlist-header"]'

SEL_SEARCH_CLICKS = [
    '[data-testid="chat-list-search"]',
    'button[aria-label*="search" i]',
    'div[aria-label*="search" i]',
    '[data-testid="search"]',
    'span[data-testid="search"]',
    'div[role="button"][title*="Search" i]',
    'p[class*="search" i]',
    'div[title*="Search or start a new chat"]',
    '._ak1r',
]

SEL_SEARCH_INPUTS = [
    'div[contenteditable="true"][data-tab="3"]',
    'div[role="textbox"][data-tab="3"]',
    '[data-testid="search-input"]',
    'div[contenteditable="true"][title*="Search" i]',
    'div[contenteditable="true"][aria-label*="Search" i]',
    'div[contenteditable="true"][data-tab="2"]',
    '#side div[contenteditable="true"]',
]

SEL_POLL_SEND_VOTE  = '[data-testid="poll-vote-send-btn"]'
SEL_VOTE_CONFIRM_FB = 'div[role="button"][aria-label*="vote" i], div[role="button"][aria-label*="send" i]'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _find_element_any(page: Page, *selectors: str, timeout: int = 3000):
    for sel in selectors:
        try:
            el = await page.wait_for_selector(sel, timeout=timeout)
            if el:
                return el
        except PWTimeoutError:
            continue
    return None


async def _scroll_chat_to_bottom(page: Page) -> None:
    await page.evaluate(
        """
        const el = document.querySelector('[data-testid="conversation-panel-messages"]')
                || document.querySelector('#main .copyable-area');
        if (el) el.scrollTop = el.scrollHeight;
        """
    )


async def _dump_dom_diagnostics(page: Page) -> None:
    info = await page.evaluate(
        """
        () => {
            const results = [];
            document.querySelectorAll('[contenteditable="true"]').forEach((el, i) => {
                const rect = el.getBoundingClientRect();
                results.push({
                    index: i, tag: el.tagName,
                    role: el.getAttribute('role'),
                    dataTab: el.getAttribute('data-tab'),
                    dataTestid: el.getAttribute('data-testid'),
                    ariaLabel: el.getAttribute('aria-label'),
                    title: el.getAttribute('title'),
                    x: Math.round(rect.x), y: Math.round(rect.y),
                    w: Math.round(rect.width), h: Math.round(rect.height),
                });
            });
            return results;
        }
        """
    )
    log.info("  DOM diagnostic -- contenteditable elements: %d", len(info))
    for el in info:
        log.info(
            "    [%d] tag=%s role=%s data-tab=%s data-testid=%s aria-label=%s title=%s pos=(%d,%d) size=%dx%d",
            el["index"], el["tag"], el["role"], el["dataTab"],
            el["dataTestid"], el["ariaLabel"], el["title"],
            el["x"], el["y"], el["w"], el["h"],
        )


async def _dump_poll_diagnostics(page: Page) -> None:
    result = await page.evaluate(
        """
        () => {
            const info = {};
            const testIds = new Set();
            document.querySelectorAll('[data-testid]').forEach(el => {
                testIds.add(el.getAttribute('data-testid'));
            });
            info.allTestIds = [...testIds].filter(id => id && (
                id.includes('poll') || id.includes('vote') || id.includes('option')
            ));
            const checkboxes = document.querySelectorAll(
                '#main [role="checkbox"], #main [role="radio"]'
            );
            info.checkboxCount = checkboxes.length;
            info.checkboxSamples = [...checkboxes].slice(0, 5).map(el => ({
                tag: el.tagName,
                role: el.getAttribute('role'),
                ariaChecked: el.getAttribute('aria-checked'),
                dataTestid: el.getAttribute('data-testid'),
                text: el.innerText.slice(0, 60),
            }));
            const voteButtons = [...document.querySelectorAll('button, div[role="button"]')]
                .filter(el =>
                    (el.getAttribute('aria-label') || '').toLowerCase().includes('vote') ||
                    (el.getAttribute('data-testid') || '').toLowerCase().includes('vote') ||
                    el.innerText.trim().toLowerCase() === 'vote'
                );
            info.voteButtonCount = voteButtons.length;
            info.voteButtonSamples = voteButtons.slice(0, 3).map(el => ({
                tag: el.tagName,
                dataTestid: el.getAttribute('data-testid'),
                ariaLabel: el.getAttribute('aria-label'),
                text: el.innerText.slice(0, 40),
            }));
            const msgContainers = document.querySelectorAll('[data-testid$="-message-container"]');
            info.msgContainerCount = msgContainers.length;
            info.msgContainerTestIds = [...new Set(
                [...msgContainers].map(el => el.getAttribute('data-testid'))
            )].slice(0, 10);
            return info;
        }
        """
    )
    log.info("  Poll DOM scan:")
    log.info("    Poll/vote data-testids on page: %s", result.get("allTestIds"))
    log.info("    Checkbox/radio elements in chat: %d", result.get("checkboxCount", 0))
    for s in result.get("checkboxSamples", []):
        log.info("      checkbox: role=%s aria-checked=%s testid=%s text=%s",
                 s["role"], s["ariaChecked"], s["dataTestid"], s["text"])
    log.info("    Vote buttons found: %d", result.get("voteButtonCount", 0))
    for s in result.get("voteButtonSamples", []):
        log.info("      vote-btn: testid=%s aria=%s text=%s",
                 s["dataTestid"], s["ariaLabel"], s["text"])
    log.info("    Message containers: %d, testids: %s",
             result.get("msgContainerCount", 0), result.get("msgContainerTestIds"))


# ---------------------------------------------------------------------------
# Session / Login
# ---------------------------------------------------------------------------

async def create_context(playwright) -> BrowserContext:
    session_path = Path(config.SESSION_DIR).resolve()
    session_path.mkdir(parents=True, exist_ok=True)
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir=str(session_path),
        headless=config.HEADLESS,
        viewport={"width": 1280, "height": 900},
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )
    return context


async def ensure_logged_in(page: Page) -> None:
    log.info("Navigating to WhatsApp Web...")
    await page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
    try:
        await page.wait_for_selector(SEL_LOGGED_IN, timeout=8000)
        log.info("Session restored -- already logged in")
        return
    except PWTimeoutError:
        pass

    log.info("Waiting for QR code scan...")
    try:
        await page.wait_for_selector(SEL_QR_SCAN_READY, timeout=20000)
        log.info("=" * 45)
        log.info("  Please scan the QR code in the browser window")
        log.info("=" * 45)
    except PWTimeoutError:
        log.warning("QR canvas not found -- waiting for login directly...")

    await page.wait_for_selector(SEL_LOGGED_IN, timeout=config.QR_TIMEOUT_SECONDS * 1000)
    log.info("Logged in successfully")


# ---------------------------------------------------------------------------
# Group Navigation
# ---------------------------------------------------------------------------

async def _focus_search_via_js(page: Page) -> bool:
    result = await page.evaluate(
        """
        () => {
            const inputs = [...document.querySelectorAll('[contenteditable="true"]')];
            const sideInputs = inputs.filter(el => {
                const rect = el.getBoundingClientRect();
                return rect.width > 10 && rect.height > 10 && rect.x < 420;
            });
            if (sideInputs.length > 0) {
                sideInputs[0].focus();
                sideInputs[0].click();
                return true;
            }
            return false;
        }
        """
    )
    return bool(result)


async def open_group(page: Page, group_name: str) -> bool:
    log.info("Looking for group: '%s'...", group_name)
    await asyncio.sleep(2)
    await page.keyboard.press("Escape")
    await asyncio.sleep(0.3)

    search_clicked = False
    for sel in SEL_SEARCH_CLICKS:
        try:
            el = await page.wait_for_selector(sel, timeout=3000)
            await el.click()
            search_clicked = True
            log.info("  Clicked search button via: %s", sel)
            break
        except PWTimeoutError:
            continue

    if not search_clicked:
        log.warning("  No search button matched -- trying JS spatial focus...")
        focused = await _focus_search_via_js(page)
        if focused:
            log.info("  JS spatial focus succeeded")
        else:
            log.warning("  JS focus also failed")

    await asyncio.sleep(0.6)

    search_input = None
    for sel in SEL_SEARCH_INPUTS:
        try:
            el = await page.wait_for_selector(sel, timeout=2000)
            if el:
                search_input = el
                log.info("  Found search input via: %s", sel)
                break
        except PWTimeoutError:
            continue

    if not search_input:
        log.warning("  Selector-based search failed -- trying JS spatial fallback...")
        await _focus_search_via_js(page)
        await asyncio.sleep(0.3)
        try:
            search_input = await page.evaluate_handle("() => document.activeElement")
            tag = await page.evaluate("el => el.tagName", search_input)
            log.info("  Active element after JS focus: %s", tag)
            if tag.lower() not in ("div", "input", "textarea"):
                search_input = None
        except Exception as e:
            log.warning("  JS active element approach failed: %s", e)
            search_input = None

    if not search_input:
        screenshot = str(Path(config.SESSION_DIR).parent / "debug_no_search_input.png")
        await page.screenshot(path=screenshot)
        await _dump_dom_diagnostics(page)
        log.error("Could not find search text box. Screenshot saved: %s", screenshot)
        return False

    await page.evaluate("el => el.focus()", search_input)
    await asyncio.sleep(0.2)
    await page.keyboard.press("Control+a")
    await page.keyboard.press("Delete")
    await asyncio.sleep(0.2)
    await page.keyboard.type(group_name, delay=80)
    log.info("  Typed group name, waiting for results...")
    await asyncio.sleep(2.5)

    result_selectors = [
        'span[title="' + group_name + '"]',
        '[data-testid="cell-frame-title"] span[title="' + group_name + '"]',
        '[title="' + group_name + '"]',
        'span[title*="' + group_name + '"]',
        '[title*="' + group_name + '"]',
    ]

    for sel in result_selectors:
        try:
            el = await page.wait_for_selector(sel, timeout=4000)
            title = await el.get_attribute("title") or group_name
            log.info("  Found group: '%s'", title)
            await el.click()
            await asyncio.sleep(1)
            await _scroll_chat_to_bottom(page)
            log.info("Opened group '%s'", title)
            return True
        except PWTimeoutError:
            continue

    screenshot = str(Path(config.SESSION_DIR).parent / "debug_group_not_found.png")
    await page.screenshot(path=screenshot)
    await _dump_dom_diagnostics(page)
    log.error("Group '%s' not found. Screenshot saved: %s", group_name, screenshot)
    return False


# ---------------------------------------------------------------------------
# Poll Detection & Voting
# ---------------------------------------------------------------------------

async def find_unvoted_polls(page: Page) -> list:
    polls = await page.evaluate(
        """
        () => {
            const results = [];
            let containers = [...document.querySelectorAll(
                '[data-testid="poll-creation-message-container"]'
            )];
            if (containers.length === 0) {
                containers = [...document.querySelectorAll('[data-testid*="poll"]')];
            }
            if (containers.length === 0) {
                containers = [...document.querySelectorAll('[data-id]')].filter(bubble => {
                    return bubble.querySelector('[role="checkbox"], [role="radio"]') !== null;
                });
            }
            containers.forEach(container => {
                const bubble = container.closest('[data-id]') || container;
                const msgId = bubble.getAttribute('data-id') || '';
                const allOptions = [
                    ...container.querySelectorAll('[role="checkbox"], [role="radio"]'),
                    ...container.querySelectorAll('[data-testid*="poll-option"]'),
                ];
                if (allOptions.length === 0) return;
                const alreadyVoted = allOptions.some(
                    el => el.getAttribute('aria-checked') === 'true'
                );
                if (alreadyVoted) return;
                results.push({ msgId: msgId, optionCount: allOptions.length });
            });
            return results;
        }
        """
    )
    return polls


async def click_poll_option_and_vote(page: Page, msg_id: str, option_index: int) -> bool:
    clicked = await page.evaluate(
        """
        ({msgId, optionIndex}) => {
            let bubble = msgId
                ? document.querySelector('[data-id="' + msgId + '"]')
                : null;
            let container = bubble || document;
            const options = [
                ...container.querySelectorAll('[role="checkbox"], [role="radio"]'),
                ...container.querySelectorAll('[data-testid*="poll-option"]'),
            ];
            if (options.length === 0 || optionIndex >= options.length) return false;
            options[optionIndex].scrollIntoView({behavior: 'smooth', block: 'center'});
            options[optionIndex].click();
            return true;
        }
        """,
        {"msgId": msg_id, "optionIndex": option_index}
    )

    if not clicked:
        log.warning("  Could not click poll option via JS")
        return False

    await asyncio.sleep(0.6)

    send_btn = await _find_element_any(
        page,
        '[data-testid="poll-vote-send-btn"]',
        '[data-testid*="vote-send"]',
        '[data-testid*="poll-send"]',
        timeout=3000,
    )

    if not send_btn:
        sent = await page.evaluate(
            """
            () => {
                const btns = [...document.querySelectorAll('div[role="button"], button')];
                const voteBtn = btns.find(el =>
                    (el.getAttribute('aria-label') || '').toLowerCase().includes('vote') ||
                    (el.getAttribute('data-testid') || '').toLowerCase().includes('vote') ||
                    el.innerText.trim().toLowerCase() === 'vote'
                );
                if (voteBtn) { voteBtn.click(); return true; }
                return false;
            }
            """
        )
        if sent:
            log.info("  Vote confirmed via JS button fallback")
            return True
        else:
            log.warning("  Could not find send/vote confirmation button")
            return False

    await send_btn.click()
    return True


async def try_vote_on_polls(page: Page, already_voted: set) -> set:
    newly_voted = set()
    polls = await find_unvoted_polls(page)
    if not polls:
        return newly_voted

    log.info("Found %d unvoted poll(s)", len(polls))

    for poll in polls:
        msg_id = poll.get("msgId", "")
        if msg_id and msg_id in already_voted:
            continue

        log.info("Voting on poll (id=%s, %d options)...", msg_id or "unknown", poll.get("optionCount", 0))
        success = await click_poll_option_and_vote(page, msg_id, config.VOTE_OPTION_INDEX)
        if success:
            log.info("  Vote sent (id=%s)", msg_id or "unknown")
            if msg_id:
                already_voted.add(msg_id)
                newly_voted.add(msg_id)
            await asyncio.sleep(1)
        else:
            log.warning("  Vote attempt failed for poll id=%s", msg_id or "unknown")

    return newly_voted


# ---------------------------------------------------------------------------
# Main Bot Loop
# ---------------------------------------------------------------------------

async def run_bot() -> None:
    log.info("Bot version: %s", __version__)
    async with async_playwright() as pw:
        log.info("Launching browser...")
        context = await create_context(pw)
        page = context.pages[0] if context.pages else await context.new_page()

        await ensure_logged_in(page)

        success = await open_group(page, config.TARGET_GROUP)
        if not success:
            log.error("Aborting -- could not open the target group.")
            await context.close()
            return

        await asyncio.sleep(2)
        await _scroll_chat_to_bottom(page)
        log.info("Running poll DOM scan on startup...")
        await _dump_poll_diagnostics(page)

        already_voted: Set[str] = set()

        log.info("Running immediate poll check...")
        await try_vote_on_polls(page, already_voted)

        log.info(
            "Monitoring '%s' every %ds. Press Ctrl+C to stop.",
            config.TARGET_GROUP,
            config.POLL_CHECK_INTERVAL,
        )

        while True:
            await asyncio.sleep(config.POLL_CHECK_INTERVAL)
            try:
                await _scroll_chat_to_bottom(page)
                await try_vote_on_polls(page, already_voted)
            except PWTimeoutError:
                log.debug("Timeout during poll check -- retrying next cycle.")
            except Exception as exc:
                log.warning("Unexpected error: %s", exc)
