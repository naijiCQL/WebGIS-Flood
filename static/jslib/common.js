// loading
var g_isLoadingStoped = false;

function g_startLoding() {
    setTimeout("g_startLoding_delay()", 3000);
}

function g_startLoding_delay() {
    if (g_isLoadingStoped)
        return;
    var loadingDiv = document.getElementById("loadingDiv");
    var loadingImage = document.getElementById("loadingImage");
    loadingDiv.style.visibility = "visible";
    loadingImage.style.left = (loadingDiv.clientWidth - loadingImage.width) * 0.5 + "px";
    loadingImage.style.top = (loadingDiv.clientHeight - loadingImage.height) * 0.5 + "px";
    g_isLoadingStoped = true;
}

function g_stopLoding() {
    g_isLoadingStoped = true;
    loadingDiv.style.visibility = "hidden";
}
