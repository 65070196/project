// ตรวจสอบว่าไฟล์ JS ถูกโหลดจริงไหม
console.log("Script.js is loaded!");

// ใช้ window.openDelete เพื่อให้มั่นใจว่าฟังก์ชันถูกเรียกใช้จาก HTML ได้แน่นอน
window.openDelete = function(url) {
    console.log("Opening modal for URL:", url);
    const modal = document.getElementById('deleteModal');
    const form = document.getElementById('deleteForm');

    if (modal && form) {
        form.action = url;
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    } else {
        console.error("หา modal หรือ form ไม่เจอ!");
    }
};

window.closeDelete = function() {
    const modal = document.getElementById('deleteModal');
    if (modal) {
        modal.classList.remove('flex');
        modal.classList.add('hidden');
    }
};
