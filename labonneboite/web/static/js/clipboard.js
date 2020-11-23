function copyToClipboard(eltId) {
    document.getElementById(eltId).select();
    try {
       document.execCommand('copy');
   } catch (err) { }
}
