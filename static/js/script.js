// ตรวจสอบว่าไฟล์ JS ถูกโหลดจริงไหม
console.log("Script.js is loaded!");

window.toggleUserMenu = function() {
    document.getElementById('userMenuDropdown').classList.toggle('hidden');
};


window.addEventListener('click', function(e) {
    if (!document.getElementById('userMenuDropdown').contains(e.target) && !e.target.closest('button[onclick="toggleUserMenu()"]')) {
        document.getElementById('userMenuDropdown').classList.add('hidden');
    }
});


// ปุ่มลบ
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



// อัปรูป
window.previewImage = function(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('image-preview').src = e.target.result;
            document.getElementById('image-preview').classList.remove('hidden');
            document.getElementById('remove-image-btn').classList.remove('hidden');
            document.getElementById('placeholder-content').classList.add('hidden');
            
            const label = document.getElementById('image-label');
            label.classList.add('p-1', 'border-solid', 'border-gray-100');
            label.classList.remove('border-dashed', 'border-gray-300');
        };
        reader.readAsDataURL(file);
    }
};

// ฟังก์ชันตอนกดปุ่มกากบาทลบรูป
window.removeImage = function(event) {
    event.preventDefault();
    event.stopPropagation();
    
    document.getElementById('image-input').value = '';
    
    document.getElementById('image-preview').classList.add('hidden');
    document.getElementById('image-preview').src = '#';
    document.getElementById('remove-image-btn').classList.add('hidden');
    document.getElementById('placeholder-content').classList.remove('hidden');
    
    const label = document.getElementById('image-label');
    label.classList.remove('p-1', 'border-solid', 'border-gray-100');
    label.classList.add('border-dashed', 'border-gray-300');
};