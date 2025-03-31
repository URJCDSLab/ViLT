
function refresh() {
    if (document.getElementById("download").checked) {
        setTimeout(() => {
        document.getElementById("select-syllabus").value = "--";
        document.getElementById("new").checked = true;
        });
    }
}