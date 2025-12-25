// Currently the background script injects code to get HTML, so this might be minimal
// But good to have for future event listening
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === "PING") {
        sendResponse("PONG");
    }
});
