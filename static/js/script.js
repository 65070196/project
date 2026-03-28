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



// อัปรูป และ เช็คขนาดรูป
window.previewImage = function(event) {
    const file = event.target.files[0];
    if (file) {
        // ตรวจสอบขนาดไฟล์ (4.5MB = 4.5 * 1024 * 1024 bytes)
        if (file.size > 4.5 * 1024 * 1024) {
            alert('ขนาดไฟล์ใหญ่เกินไป กรุณาอัปโหลดรูปภาพขนาดไม่เกิน 4.5MB');
            event.target.value = ''; // เคลียร์ไฟล์ที่เลือกออก
            return; // หยุดการทำงาน
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            // 1. แสดงรูปภาพพรีวิว
            document.getElementById('image-preview').src = e.target.result;
            document.getElementById('image-preview').classList.remove('hidden');
            
            // 2. แสดงปุ่มลบ
            document.getElementById('remove-image-btn').classList.remove('hidden');
            
            // 3. ซ่อนข้อความ Placeholder (อัปโหลดรูปภาพ)
            document.getElementById('placeholder-content').classList.add('hidden');
            
            // 4. เปลี่ยนสไตล์กรอบจากเส้นปะเป็นเส้นทึบให้ดูสวยงาม
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


window.filterQueue = function(status) {
    const allBtns = document.querySelectorAll('.filter-btn');
    allBtns.forEach(btn => {
        btn.classList.remove('bg-indigo-600', 'text-white', 'shadow-sm');
        btn.classList.add('text-gray-600');
    });

    const activeBtn = document.getElementById('btn-' + status);
    activeBtn.classList.remove('text-gray-600');
    activeBtn.classList.add('bg-indigo-600', 'text-white', 'shadow-sm');

    const rows = document.querySelectorAll('.queue-row');
    let visibleCount = 0;

    rows.forEach(row => {
        if (status === 'all' || row.dataset.status === status) {
        row.style.display = 'grid'; 
        visibleCount++;
        } else {
        row.style.display = 'none'; 
        }
    });

    const filterEmptyState = document.getElementById('filterEmptyState');
    const noDataEmpty = document.getElementById('noDataEmpty');

    if (noDataEmpty) {
        return; 
    }

    if (visibleCount === 0) {
        filterEmptyState.classList.remove('hidden');
        filterEmptyState.classList.add('block');
    } else {
        filterEmptyState.classList.remove('block');
        filterEmptyState.classList.add('hidden');
    }
}
