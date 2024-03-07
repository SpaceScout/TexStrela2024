var brightnessInPercentage = 100
var contrastInPercentage = 100


function myFunction() {
    num = num + 1
    alert(num)
}

function changeBrightness(bValue) {
    brightnessInPercentage = bValue;
    document.getElementById("imageforchanging").style = "filter: brightness("+brightnessInPercentage+"%) contrast("+contrastInPercentage+"%)";
    document.getElementById("spanBrightnessValue").textContent=bValue+"%";
}

function changeContrast(cValue) {
    contrastInPercentage = cValue;
    document.getElementById("imageforchanging").style = "filter: brightness("+brightnessInPercentage+"%) contrast("+contrastInPercentage+"%)";
    document.getElementById("spanContrastValue").textContent=cValue+"%";
}