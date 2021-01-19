function copyToClipboard(eltId) {
    ga('send', 'event', 'Clipboard', 'copy');
    document.getElementById(eltId).select();
    try {
       document.execCommand('copy');
   } catch (err) { }
}
