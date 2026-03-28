// ตรวจสอบว่าไฟล์ JS ถูกโหลดจริงไหม
console.log("Script.js is loaded!");

// ==========================================
// 1. ระบบเมนูผู้ใช้ (Dropdown Profile)
// ==========================================
window.toggleUserMenu = function() {
    const menu = document.getElementById('userMenuDropdown');
    if (menu) menu.classList.toggle('hidden');
};

window.addEventListener('click', function(e) {
    const menu = document.getElementById('userMenuDropdown');
    const btn = e.target.closest('button[onclick="toggleUserMenu()"]');
    if (menu && !menu.contains(e.target) && !btn) {
        menu.classList.add('hidden');
    }
});

// ==========================================
// 2. ระบบแจ้งเตือนยืนยันการลบ (Delete Modal)
// ==========================================
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

// ==========================================
// 3. ระบบอัปโหลดและพรีวิวรูปภาพ (จำกัดขนาด 4.5MB)
// ==========================================
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
            if(label) {
                label.classList.add('p-1', 'border-solid', 'border-gray-100');
                label.classList.remove('border-dashed', 'border-gray-300');
            }
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
    if(label) {
        label.classList.remove('p-1', 'border-solid', 'border-gray-100');
        label.classList.add('border-dashed', 'border-gray-300');
    }
};

// ==========================================
// 4. ระบบกรองสถานะคิว (Filter Queue) - ใช้ได้ทั้งฝั่งร้านและลูกค้า
// ==========================================
window.filterQueue = function(status) {
    const allBtns = document.querySelectorAll('.filter-btn');
    allBtns.forEach(btn => {
        btn.classList.remove('bg-indigo-600', 'text-white', 'shadow-sm');
        btn.classList.add('text-gray-600');
    });

    const activeBtn = document.getElementById('btn-' + status);
    if(activeBtn) {
        activeBtn.classList.remove('text-gray-600');
        activeBtn.classList.add('bg-indigo-600', 'text-white', 'shadow-sm');
    }

    // รองรับทั้งคลาส .queue-row (ฝั่งร้านค้า) และ .queue-card (ฝั่งลูกค้า)
    const rows = document.querySelectorAll('.queue-row, .queue-card');
    let visibleCount = 0;

    rows.forEach(row => {
        if (status === 'all' || row.dataset.status === status) {
            row.style.display = ''; // เคลียร์ Inline Style ทิ้ง เพื่อให้มันกลับไปใช้ CSS Grid/Flex ปกติ
            visibleCount++;
        } else {
            row.style.display = 'none'; 
        }
    });

    const filterEmptyState = document.getElementById('filterEmptyState');
    const noDataEmpty = document.getElementById('noDataEmpty');

    if (noDataEmpty) {
        return; // ถ้าไม่มีคิวในระบบเลยตั้งแต่ต้น ไม่ต้องทำอะไรต่อ
    }

    if (filterEmptyState) {
        if (visibleCount === 0) {
            filterEmptyState.classList.remove('hidden');
            // เช็คว่าต้องโชว์แบบ flex หรือ block
            if (filterEmptyState.classList.contains('flex-col')) {
                filterEmptyState.classList.add('flex');
            } else {
                filterEmptyState.classList.add('block');
            }
        } else {
            filterEmptyState.classList.remove('block', 'flex');
            filterEmptyState.classList.add('hidden');
        }
    }
};

// ==========================================
// 5. ระบบค้นหา Real-time (Live Search ฝั่งลูกค้า)
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchDropdown = document.getElementById('searchDropdown');
    const searchList = document.getElementById('searchList');

    if (searchInput && searchDropdown && searchList) {
        searchInput.addEventListener('input', async function() {
            const query = this.value.trim();
            
            if (query.length > 0) {
                try {
                    const response = await fetch(`/api/search-suggestion/?q=${encodeURIComponent(query)}`);
                    const data = await response.json();
                    
                    searchList.innerHTML = ''; 
                    
                    if (data.results.length > 0) {
                        data.results.forEach(shop => {
                            const li = document.createElement('li');
                            li.innerHTML = `
                                <a href="/shop-detail/${shop.shop_id}/" class="block px-4 py-3 hover:bg-[#a7a1f9]/10 text-black text-sm transition-colors cursor-pointer flex items-center gap-2">
                                    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                                    ${shop.shop_name}
                                </a>
                            `;
                            searchList.appendChild(li);
                        });
                    } else {
                        searchList.innerHTML = `<li class="px-4 py-3 text-gray-400 text-sm italic">ไม่พบร้านค้าที่ค้นหา...</li>`;
                    }
                    
                    searchDropdown.classList.remove('hidden'); 
                } catch (error) {
                    console.error('Search error:', error);
                }
            } else {
                searchDropdown.classList.add('hidden');
            }
        });

        // ซ่อนกล่องค้นหาเมื่อคลิกที่อื่น
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
                searchDropdown.classList.add('hidden');
            }
        });
    }
});