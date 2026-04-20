const ARABIC_DIGIT_MAP = {
  '١':'1','٢':'2','٣':'3','٤':'4','٥':'5',
  '٦':'6','٧':'7','٨':'8','٩':'9'
};

const ARABIC_LETTER_MAP = {
  'أ':'A','ب':'B','ج':'G','د':'D','ر':'R',
  'س':'S','ص':'C','ط':'T','ع':'E','ف':'F',
  'ق':'K','ل':'L','م':'M','ن':'N','ه':'H',
  'هـ':'H','و':'W','ى':'Y','ي':'Y'
};

window.AppConfig = null;

document.addEventListener('DOMContentLoaded', async () => {
    // 0. Language Initialization
    const savedLang = localStorage.getItem('aman_lang');
    if (savedLang) {
        applyLanguage(savedLang);
        const overlay = document.getElementById('lang-overlay');
        if (overlay) overlay.style.display = 'none';
    } else {
        const overlay = document.getElementById('lang-overlay');
        if (overlay) overlay.style.display = 'flex';
    }

    document.getElementById('lang-ar').onclick = () => {
        applyLanguage('ar');
        const overlay = document.getElementById('lang-overlay');
        if (overlay) overlay.style.display = 'none';
    };

    document.getElementById('lang-en').onclick = () => {
        applyLanguage('en');
        const overlay = document.getElementById('lang-overlay');
        if (overlay) overlay.style.display = 'none';
    };

    const toggleBtn = document.getElementById('btn-lang-toggle');
    if (toggleBtn) {
        toggleBtn.onclick = () => {
            const current = localStorage.getItem('aman_lang') || 'en';
            const opposite = current === 'ar' ? 'en' : 'ar';
            applyLanguage(opposite);
        };
    }

    // 1. Fetch Config
    try {
        const res = await fetch('/config');
        window.AppConfig = await res.json();
        populateConfig(window.AppConfig);
        applyLanguage(localStorage.getItem('aman_lang') || 'en');
    } catch(e) {
        console.error("Failed to load config", e);
    }

    // 2. Tab Navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // 3. Initialize Camera Tab
    switchTab('tab-scan');
});

function applyLanguage(lang) {
  const isAr = lang === 'ar';
  document.documentElement.setAttribute('dir', isAr ? 'rtl' : 'ltr');
  document.documentElement.setAttribute('lang', lang);
  
  document.querySelectorAll('.text-en').forEach(el => {
    el.style.display = isAr ? 'none' : '';
  });
  document.querySelectorAll('.text-ar').forEach(el => {
    el.style.display = isAr ? '' : 'none';
  });
  
  localStorage.setItem('aman_lang', lang);
  
  const toggleBtn = document.getElementById('btn-lang-toggle');
  if(toggleBtn) {
    toggleBtn.textContent = isAr ? 'EN' : 'عربي';
  }
}

function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    
    document.getElementById(tabId).classList.add('active');
    const btn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
    if(btn) btn.classList.add('active');

    if(tabId === 'tab-hotspots') loadHotspots();
}

function populateConfig(cfg) {
    // Categories
    const catSelect = document.getElementById('report-category');
    catSelect.innerHTML = cfg.categories.map(c => `<option value="${c}">${c}</option>`).join('');

    // Severities
    const sevContainer = document.getElementById('severity-options');
    if (sevContainer && cfg.severities) {
        sevContainer.innerHTML = cfg.severities.map(s => {
            document.documentElement.style.setProperty(`--sev-${s.level}-color`, s.color_hex);
            return `
                <div class="seg-option" data-val="${s.level}" style="border-color:${s.color_hex}; color:${s.color_hex}" onclick="selectSeverity(${s.level}, this)">
                    ${s.icon} <span class="text-en">${s.label_en || s.label_ar}</span><span class="text-ar" style="display:none">${s.label_ar}</span>
                </div>
            `;
        }).join('');
        
        if(cfg.severities.length > 0) {
            selectSeverity(cfg.severities[0].level, sevContainer.children[0]);
        }
    }
}

let selectedSeverity = 1;
window.selectSeverity = function(val, el) {
    selectedSeverity = val;
    document.querySelectorAll('.seg-option').forEach(o => {
        o.classList.remove('selected');
        o.style.backgroundColor = 'transparent';
    });
    el.classList.add('selected');
    el.style.backgroundColor = el.style.borderColor + '20';
};

/* ================================
   TAB 1: SCAN & CAMERA
   ================================ */
const state = { active: false, stream: null };
const els = {
    vid: document.getElementById('camera-video'),
    cvs: document.getElementById('camera-canvas'),
    btnCam: document.getElementById('btn-camera'),
    btnUp: document.getElementById('btn-upload'),
    btnCap: document.getElementById('btn-capture-photo'),
    file: document.getElementById('file-input'),
    res: document.getElementById('results-cards'),
    noRes: document.getElementById('no-results'),
    imgCont: document.getElementById('detection-image-container'),
    img: document.getElementById('detection-image')
};

els.btnCam.onclick = async () => {
    if(state.active) {
        state.stream.getTracks().forEach(t=>t.stop());
        els.vid.srcObject = null;
        state.active = false;
        els.btnCam.textContent = 'تشغيل';
        els.btnCap.disabled = true;
    } else {
        const constraints = {
            video: {
                facingMode: 'environment',
                width: { ideal: 1920 },
                height: { ideal: 1080 },
                zoom: true
            }
        };
        state.stream = await navigator.mediaDevices.getUserMedia(constraints).catch(e => null);
        if(state.stream) {
            els.vid.srcObject = state.stream;
            state.active = true;
            els.btnCam.textContent = 'إيقاف';
            els.btnCap.disabled = false;
            
            // Wire zoom slider
            const track = state.stream.getVideoTracks()[0];
            const capabilities = track.getCapabilities();
            const slider = document.getElementById('zoom-slider');
            const label = document.getElementById('zoom-label');
            
            if (capabilities.zoom) {
                slider.min = capabilities.zoom.min || 1;
                slider.max = capabilities.zoom.max || 5;
                slider.step = capabilities.zoom.step || 0.1;
                slider.value = track.getSettings().zoom || 1;
                label.textContent = parseFloat(slider.value).toFixed(1) + 'x';
                
                slider.oninput = function() {
                    track.applyConstraints({ advanced: [{ zoom: this.value }] });
                    label.textContent = parseFloat(this.value).toFixed(1) + 'x';
                };
            } else {
                slider.disabled = true; // Devices that don't support zoom API
            }
        }
    }
};

els.btnUp.onclick = () => els.file.click();

function scaleDown(imgSource, originalW, originalH, callback) {
    const maxDimension = 640;
    let w = originalW, h = originalH;
    if (w > maxDimension || h > maxDimension) {
        if (w > h) { h = Math.round(h * maxDimension / w); w = maxDimension; }
        else { w = Math.round(w * maxDimension / h); h = maxDimension; }
    }
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    c.getContext('2d').drawImage(imgSource, 0, 0, w, h);
    callback(c.toDataURL('image/jpeg', 0.8));
}

els.file.onchange = (e) => {
    if(!e.target.files[0]) return;
    const r = new FileReader();
    r.onload = (ev) => {
        const img = new Image();
        img.onload = () => scaleDown(img, img.width, img.height, analyze);
        img.src = ev.target.result;
    };
    r.readAsDataURL(e.target.files[0]);
};

els.btnCap.onclick = () => {
    if(!state.active) return;
    scaleDown(els.vid, els.vid.videoWidth, els.vid.videoHeight, analyze);
};

window.currentGovernorate = 'Unknown';

window.getPlateText = function() {
    const d = document.getElementById('plate-digits').value;
    let l = document.getElementById('plate-l1').value + document.getElementById('plate-l2').value + document.getElementById('plate-l3').value;
    return (d && l) ? (d + '-' + l) : (d || l);
};

window.classifyPlateLocally = function() {
    const d = document.getElementById('plate-digits').value;
    const l = document.getElementById('plate-l1').value + document.getElementById('plate-l2').value + document.getElementById('plate-l3').value;
    let gov = "";
    
    const SUFFIX = {
        'S':'Alexandria - الاسكندرية', 'K':'Qalyubia - القليوبية', 'R':'Sharqia - الشرقية', 'M':'Monufia - المنوفية', 'B':'Beheira - البحيرة',
        'D':'Dakahlia - الدقهلية', 'E':'Gharbia - الغربية', 'L':'Kafr El Sheikh - كفر الشيخ', 'F':'Faiyum - الفيوم',
        'W':'Beni Suef - بني سويف', 'N':'Minya - المنيا', 'Y':'Asyut - أسيوط', 'H':'Sohag - سوهاج'
    };
    const PREFIX = {
        'CA':'Qena - قنا', 'CK':'Luxor - الأقصر', 'CW':'Aswan - أسوان', 'TD':'Damietta - دمياط', 'TE':'Port Said - بورسعيد',
        'TC':'Ismailia - الإسماعيلية', 'TS':'Suez - السويس', 'TR':'Red Sea - البحر الأحمر', 'TA':'North Sinai - شمال سيناء',
        'TG':'South Sinai - جنوب سيناء', 'GH':'Matrouh - مطروح', 'GB':'New Valley - الوادي الجديد'
    };
    
    if (d.length === 3) gov = "Cairo - القاهرة";
    else if (l.length === 2 && l) gov = "Giza - الجيزة";
    else if (l.length === 3) {
        const pref = l.slice(0,2);
        const suff = l.slice(-1);
        if (PREFIX[pref]) gov = PREFIX[pref];
        else if (SUFFIX[suff]) gov = SUFFIX[suff];
    }
    
    const govDisplay = document.getElementById('plate-gov-display');
    if (gov) {
        govDisplay.textContent = gov;
        window.currentGovernorate = gov.split(' - ')[0]; 
    } else {
        govDisplay.textContent = "";
        window.currentGovernorate = "Unknown";
    }
};

window.setReportPlate = function(plateText) {
    const parts = plateText.split('-');
    if(parts.length >= 2) {
        const d = parts[0].replace(/[^1-9]/g, '').substring(0,4);
        const chars = parts[1].replace(/[^A-Za-z]/g, '').toUpperCase();
        
        document.getElementById('plate-digits').value = d;
        document.getElementById('plate-l1').value = chars[0] || '';
        document.getElementById('plate-l2').value = chars[1] || '';
        document.getElementById('plate-l3').value = chars[2] || '';
    } else {
        document.getElementById('plate-digits').value = plateText.replace(/[^1-9]/g, '').substring(0,4);
        document.getElementById('plate-l1').value = '';
        document.getElementById('plate-l2').value = '';
        document.getElementById('plate-l3').value = '';
    }
    classifyPlateLocally();
};

window.reportThisPlate = function(plateText) {
    setReportPlate(plateText);
    switchTab('tab-report');
};

async function analyze(b64) {
    els.noRes.style.display = 'block';
    els.noRes.innerHTML = '<p><span class="text-en">Analyzing... ⏳</span><span class="text-ar" style="display:none">جاري التحليل... ⏳</span></p>';
    applyLanguage(localStorage.getItem('aman_lang') || 'en');
    els.res.style.display = 'none';
    els.imgCont.style.display = 'none';

    try {
        const res = await fetch('/api/detect-frame', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({image:b64})
        }).then(r=>r.json());
        
        if (res.error) {
            els.noRes.innerHTML = `<p>Error: ${res.error}</p>`;
            return;
        }

        if (!res.plates || res.plates.length === 0) {
            els.noRes.innerHTML = '<p><span class="text-en">No plates detected</span><span class="text-ar" style="display:none">لم يتم الكشف عن لوحات</span></p>';
            applyLanguage(localStorage.getItem('aman_lang') || 'en');
        } else {
            els.noRes.style.display = 'none';
            els.res.style.display = 'block';
            
            const renderedCards = await Promise.all(res.plates.map(async p => {
                const text = p.plate_text || p.full_text || p.raw_text || '';
                let hasReports = false; let maxSeverity = 0; let maxCategory = '';
                try {
                    const rRes = await fetch(`/plate/${encodeURIComponent(text)}`);
                    if(rRes.ok) {
                        const rData = await rRes.json();
                        if(rData.reports && rData.reports.length > 0) {
                            hasReports = true;
                            maxSeverity = rData.reports[0].severity;
                            maxCategory = rData.reports[0].category;
                        }
                    }
                } catch(e) {}
                
                return `
                <div class="plate-card">
                    <div class="plate-text">${text}</div>
                    <div class="info-grid">
                        <div><div class="info-label">المحافظة / Gov</div>${p.governorate || p.governorate_ar || 'Unknown'}</div>
                        <div><div class="info-label">النوع / Type</div>${p.vehicle_type || p.vehicle_type_ar || 'Unknown'}</div>
                        <div><div class="info-label">الثقة / Conf</div>${p.overall_confidence ? Math.round(p.overall_confidence*100) + '%' : 'N/A'}</div>
                    </div>
                    ${hasReports ? `
                    <div class="msg-banner msg-error" style="margin-top:10px;margin-bottom:10px;padding:8px;"><span class="text-en">⚠️ Plate has active community reports!</span><span class="text-ar" style="display:none">⚠️ توجد بلاغات نشطة حول هذه اللوحة!</span></div>
                    <button class="btn-primary" onclick="generateWarningCard('${text.replace(/'/g, "\\'")}', '${p.governorate || 'Unknown'}', ${maxSeverity}, '${maxCategory.replace(/'/g, "\\'")}')" style="margin-bottom:10px; background:#F44336; border-color:#F44336; width:100%;"><span class="text-en">Share Warning</span><span class="text-ar" style="display:none">مشاركة التحذير</span></button>
                    ` : ''}
                    <button class="report-btn" onclick="reportThisPlate('${text.replace(/'/g, "\\'")}')"><span class="text-en">Report Plate</span><span class="text-ar" style="display:none">الإبلاغ عن هذه اللوحة</span></button>
                </div>
                `;
            }));
            
            els.res.innerHTML = renderedCards.join('');
            applyLanguage(localStorage.getItem('aman_lang') || 'en');
        }
        
        if(res.annotated_image) {
            els.img.src = `data:image/jpeg;base64,${res.annotated_image}`;
            els.imgCont.style.display = 'block';
        }
    } catch(e) {
        els.noRes.innerHTML = `<p>خطأ في الاتصال بالخادم / Connection error</p>`;
    }
}

/* ================================
   TAB 2: REPORT
   ================================ */
const descInput = document.getElementById('report-desc');
descInput.addEventListener('input', () => {
    document.getElementById('desc-count').textContent = descInput.value.length;
});

// Setup Input Listeners
const validLetters = ['A', 'B', 'G', 'D', 'R', 'S', 'C', 'T', 'E', 'F', 'K', 'L', 'M', 'N', 'H', 'W', 'Y'];
const pDigits = document.getElementById('plate-digits');
const pl1 = document.getElementById('plate-l1');
const pl2 = document.getElementById('plate-l2');
const pl3 = document.getElementById('plate-l3');

pDigits.addEventListener('input', function() {
    let newVal = '';
    for (let char of this.value) {
        if (ARABIC_DIGIT_MAP[char]) {
            newVal += ARABIC_DIGIT_MAP[char];
        } else if (/[1-9]/.test(char)) {
            newVal += char;
        }
    }
    this.value = newVal;
    if (this.value.length === 4) pl1.focus();
    classifyPlateLocally();
});

function handleLetterInput(el, nextEl, prevEl) {
    el.addEventListener('input', function() {
        let val = this.value;
        if (!val) {
           classifyPlateLocally();
           return;
        }
        
        let mapped = ARABIC_LETTER_MAP[val] || val.toUpperCase();
        
        if (!validLetters.includes(mapped)) {
            this.value = '';
        } else {
            this.value = mapped;
            if(nextEl && this.value) nextEl.focus();
        }
        classifyPlateLocally();
    });
    el.addEventListener('keydown', function(e) {
        if(e.key === 'Backspace' && !this.value && prevEl) {
            prevEl.focus();
            e.preventDefault();
        }
    });
}
handleLetterInput(pl1, pl2, pDigits);
handleLetterInput(pl2, pl3, pl1);
handleLetterInput(pl3, null, pl2);

document.getElementById('report-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const plate = window.getPlateText();
    
    const msg = document.getElementById('report-msg');
    
    if(!document.getElementById('plate-digits').value) {
        msg.className = 'msg-banner msg-error';
        msg.innerHTML = '<span class="text-en">Digits field cannot be empty</span><span class="text-ar" style="display:none">حقل الأرقام لا يمكن أن يكون فارغاً</span>';
        msg.style.display = 'block';
        applyLanguage(localStorage.getItem('aman_lang') || 'en');
        return;
    }
    
    const cat = document.getElementById('report-category').value;
    const desc = descInput.value;
    
    msg.style.display = 'none';
    const btn = document.getElementById('btn-submit-report');
    btn.disabled = true;
    
    try {
        const res = await fetch('/report', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                plate_text: plate,
                category: cat,
                description: desc,
                reported_by: "anonymous",
                governorate: window.currentGovernorate || "Unknown"
            })
        });
        
        const data = await res.json();
        
        if(res.ok) {
            msg.className = 'msg-banner msg-success';
            msg.textContent = `تم الإبلاغ بنجاح! Report ID: ${data.report_id}`;
            document.getElementById('report-form').reset();
            document.getElementById('plate-digits').value = '';
            document.getElementById('plate-l1').value = '';
            document.getElementById('plate-l2').value = '';
            document.getElementById('plate-l3').value = '';
            classifyPlateLocally();
            document.getElementById('desc-count').textContent = '0';
            
            setTimeout(() => {
                msg.style.display = 'none';
                switchTab('tab-scan');
            }, 3000);
        } else {
            msg.className = 'msg-banner msg-error';
            msg.textContent = `Error: ${data.detail || data.message || 'Failed'}`;
        }
    } catch(e) {
        msg.className = 'msg-banner msg-error';
        msg.textContent = 'Connection error';
    } finally {
        msg.style.display = 'block';
        btn.disabled = false;
    }
});

/* ================================
   TAB 3: LOOKUP
   ================================ */
const timeAgo = (iso) => {
    const diff = (new Date() - new Date(iso)) / 1000;
    if(diff < 60) return "Just now";
    if(diff < 3600) return Math.floor(diff/60) + " mins ago";
    if(diff < 86400) return Math.floor(diff/3600) + " hours ago";
    return Math.floor(diff/86400) + " days ago";
};

// Setup Lookup Bubble Inputs
const lkDigits = document.getElementById('lookup-digits');
const lkL1 = document.getElementById('lookup-l1');
const lkL2 = document.getElementById('lookup-l2');
const lkL3 = document.getElementById('lookup-l3');

lkDigits.addEventListener('input', function() {
    let newVal = '';
    for (let char of this.value) {
        if (ARABIC_DIGIT_MAP[char]) newVal += ARABIC_DIGIT_MAP[char];
        else if (/[1-9]/.test(char)) newVal += char;
    }
    this.value = newVal;
    if (this.value.length === 4) lkL1.focus();
});

function handleLookupLetterInput(el, nextEl, prevEl) {
    el.addEventListener('input', function() {
        let val = this.value;
        if (!val) return;
        let mapped = ARABIC_LETTER_MAP[val] || val.toUpperCase();
        if (!validLetters.includes(mapped)) {
            this.value = '';
        } else {
            this.value = mapped;
            if(nextEl && this.value) nextEl.focus();
        }
    });
    el.addEventListener('keydown', function(e) {
        if(e.key === 'Backspace' && !this.value && prevEl) {
            prevEl.focus();
            e.preventDefault();
        }
    });
}
handleLookupLetterInput(lkL1, lkL2, lkDigits);
handleLookupLetterInput(lkL2, lkL3, lkL1);
handleLookupLetterInput(lkL3, null, lkL2);

function getLookupPlateText() {
    const d = lkDigits.value;
    const l = lkL1.value + lkL2.value + lkL3.value;
    return (d && l) ? (d + '-' + l) : (d || l);
}

document.getElementById('btn-lookup').onclick = async () => {
    const plate = getLookupPlateText();
    if(!plate) return;
    
    const spin = document.getElementById('lookup-loading');
    const msg = document.getElementById('lookup-msg');
    const list = document.getElementById('lookup-results');
    
    spin.style.display = 'block';
    msg.style.display = 'none';
    list.innerHTML = '';
    
    try {
        const res = await fetch(`/plate/${encodeURIComponent(plate)}`);
        const data = await res.json();
        
        if(!res.ok) throw new Error(data.detail);
        
        if(!data.reports || data.reports.length === 0) {
            msg.className = 'msg-banner';
            msg.innerHTML = '<span class="text-en">No reports found for this plate</span><span class="text-ar" style="display:none">لا توجد بلاغات لهذه اللوحة</span>';
            msg.style.display = 'block';
            applyLanguage(localStorage.getItem('aman_lang') || 'en');
        } else {
            let severityHeader = '';
            try {
                const sevRes = await fetch(`/plate/${encodeURIComponent(plate)}/severity`);
                if(sevRes.ok) {
                    const sevData = await sevRes.json();
                    const sInfo = sevData.severity_info;
                    const sColor = sInfo.color_hex || '#888';
                    severityHeader = `
                        <div class="current-threat-level" style="background:${sColor}20; border:2px solid ${sColor}; padding:15px; border-radius:10px; margin-bottom:20px; text-align:center;">
                            <div style="font-size:0.9rem; color:${sColor}; font-weight:bold; margin-bottom:5px;">Current Threat Level | مستوى الخطر الحالي</div>
                            <div style="font-size:1.5rem; color:#fff; font-weight:bold;">${sInfo.icon} ${sInfo.label_ar} | ${sInfo.label_en}</div>
                            <div style="font-size:0.85rem; color:#aaa; margin-top:5px;">Based on ${sevData.report_count} active reports</div>
                        </div>
                    `;
                }
            } catch(e) { console.error('Failed to load severity', e); }
            
            list.innerHTML = severityHeader + data.reports.map(r => renderReportCard(r)).join('');
        }
    } catch(e) {
        msg.className = 'msg-banner msg-error';
        msg.textContent = 'Error loading reports';
        msg.style.display = 'block';
    } finally {
        spin.style.display = 'none';
    }
};

window.confirmReport = async (reportId, btn) => {
    btn.disabled = true;
    btn.innerHTML = '<span class="text-en">Confirming...</span><span class="text-ar" style="display:none">جاري التأكيد...</span>';
    applyLanguage(localStorage.getItem('aman_lang') || 'en');
    try {
        const res = await fetch(`/report/${reportId}/confirm`, { method: 'POST' });
        if(res.ok) btn.innerHTML = '<span class="text-en">Confirmed ✓</span><span class="text-ar" style="display:none">تم التأكيد ✓</span>';
        else btn.innerHTML = '<span class="text-en">Failed</span><span class="text-ar" style="display:none">فشل</span>';
    } catch(e) {
        btn.innerHTML = '<span class="text-en">Error</span><span class="text-ar" style="display:none">خطأ</span>';
    }
    applyLanguage(localStorage.getItem('aman_lang') || 'en');
};

function renderReportCard(r) {
    const sev = window.AppConfig?.severities.find(s => s.level === r.severity) || {};
    const color = sev.color_hex || '#888';
    // ensure UTC processing for iso parsing
    const dateStr = timeAgo(r.timestamp + (r.timestamp.endsWith('Z') ? '' : 'Z'));
    const desc = r.description ? (r.description.length > 100 ? r.description.substring(0, 100) + '...' : r.description) : 'No details';
    const safeText = (r.plate_text || '').replace(/'/g, "\\'");
    const safeGov = (r.governorate || 'Unknown').replace(/'/g, "\\'");
    const safeCat = (r.category || 'Warning').replace(/'/g, "\\'");
    
    return `
        <div class="report-card">
            <div class="report-meta">
                <span class="badge" style="background:${color}">${sev.icon || ''} ${sev.label_ar || 'N/A'}</span>
                <span class="report-time">${dateStr}</span>
            </div>
            <div style="font-weight:bold">${r.category}</div>
            <div class="report-desc">${desc}</div>
            <div class="report-meta">
                <span style="font-size:0.8rem;color:#888">Confirmed: ${r.confirmed_count}</span>
            </div>
            ${(!r.status || r.status === 'active') ? `<button class="btn-primary" onclick="generateWarningCard('${safeText}', '${safeGov}', ${r.severity}, '${safeCat}')" style="width:100%;margin-bottom:5px;background:${color};border-color:${color}"><span class="text-en">Share Warning</span><span class="text-ar" style="display:none">مشاركة التحذير</span></button>` : ''}
            <button class="btn-confirm" onclick="confirmReport(${r.id}, this)"><span class="text-en">Confirm</span><span class="text-ar" style="display:none">تأكيد</span></button>
        </div>
    `;
}

/* ================================
   TAB 4: HOTSPOTS
   ================================ */
document.getElementById('btn-refresh-hotspots').onclick = loadHotspots;

async function loadHotspots() {
    const spin = document.getElementById('hotspots-loading');
    const msg = document.getElementById('hotspots-msg');
    const list = document.getElementById('hotspots-list');
    
    if(list.innerHTML === '') spin.style.display = 'block';
    msg.style.display = 'none';
    
    try {
        const res = await fetch('/hotspots?min_reports=2');
        const data = await res.json();
        
        if(!res.ok) throw new Error();
        
        if(!data.hotspots || data.hotspots.length === 0) {
            msg.className = 'msg-banner';
            msg.innerHTML = "لا توجد لوحات خطرة حالياً<br>No hotspots yet";
            msg.style.display = 'block';
            list.innerHTML = '';
        } else {
            list.innerHTML = data.hotspots.map((h, i) => {
                const sev = window.AppConfig?.severities.find(s => s.level === h.max_severity) || {};
                const color = sev.color_hex || '#888';
                return `
                <div class="report-card" style="display:flex;align-items:center;gap:15px">
                    <div style="font-size:1.5rem;font-weight:bold;color:#888;min-width:30px">#${i+1}</div>
                    <div style="flex:1">
                        <div class="plate-text" style="text-align:right;margin-bottom:5px;font-size:1.2rem;letter-spacing:normal">${h.plate_text}</div>
                        <div style="font-size:0.85rem;color:#aaa">${h.governorate} • ${h.report_count} reports</div>
                    </div>
                    <div>
                        <span class="badge" style="background:${color}">${sev.icon || '!'} Max ${sev.label_en || ''}</span>
                    </div>
                </div>
                `;
            }).join('');
        }
        
        if(!document.getElementById('dev-test-container')) {
            const devBox = document.createElement('div');
            devBox.id = 'dev-test-container';
            devBox.innerHTML = `
                <div style="text-align:center; margin-top:20px; border-top:1px solid rgba(255,255,255,0.1); padding-top:15px;">
                    <div style="font-size:0.7rem; color:#888; margin-bottom:5px;">Dev Test</div>
                    <button class="btn-primary" style="background:transparent; color:#aaa; border:1px solid #aaa;" onclick="generateWarningCard('1234-NMS', 'Cairo', 3, 'Suspicious')">Test Warning Card | اختبار البطاقة</button>
                </div>
            `;
            document.getElementById('tab-hotspots').appendChild(devBox);
        }
    } catch(e) {
        msg.className = 'msg-banner msg-error';
        msg.textContent = 'Error loading hotspots';
        msg.style.display = 'block';
    } finally {
        spin.style.display = 'none';
    }
}

/* ================================
   PWA INSTALL
   ================================ */
let deferredPrompt;
const btnInstall = document.getElementById('btn-install');

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if(btnInstall) btnInstall.style.display = 'block';
});

if(btnInstall) {
    btnInstall.addEventListener('click', async () => {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            if (outcome === 'accepted') {
                btnInstall.style.display = 'none';
            }
            deferredPrompt = null;
        }
    });
}

/* ================================
   WARNING CARD GENERATOR
   ================================ */
window.generateWarningCard = async function(plateText, governorate, severity, category) {
    try {
        const sevInfo = window.AppConfig?.severities.find(s => s.level === severity) || {
            color_hex: '#888', icon: '⚠️', label_ar: 'غير محدد', label_en: 'Unknown'
        };
        
        let r=0,g=0,b=0;
        if(sevInfo.color_hex.startsWith('#')){
            const hex = sevInfo.color_hex.substring(1);
            r = parseInt(hex.substring(0,2), 16);
            g = parseInt(hex.substring(2,4), 16);
            b = parseInt(hex.substring(4,6), 16);
        }
        r = Math.floor(r * 0.8);
        g = Math.floor(g * 0.8);
        b = Math.floor(b * 0.8);
        const bgColor = `rgb(${r},${g},${b})`;
        
        const canvas = document.createElement('canvas');
        canvas.width = 800;
        canvas.height = 450;
        const ctx = canvas.getContext('2d');
        
        ctx.fillStyle = bgColor;
        ctx.fillRect(0, 0, 800, 450);
        
        ctx.fillStyle = 'rgba(0,0,0,0.2)';
        ctx.fillRect(0, 0, 800, 80);
        
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 28px Cairo, system-ui, sans-serif';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText('أمان | Aman', 30, 40);
        
        ctx.font = '22px Cairo, system-ui, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(`${sevInfo.icon} ${sevInfo.label_ar} | ${sevInfo.label_en}`, 770, 40);
        
        ctx.font = 'bold 72px Cairo, system-ui, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(plateText, 400, 190);
        
        ctx.font = '24px Cairo, system-ui, sans-serif';
        ctx.fillText(governorate, 400, 260);
        
        ctx.fillStyle = 'rgba(255,255,255,0.7)';
        ctx.font = '18px Cairo, system-ui, sans-serif';
        ctx.fillText(category, 400, 310);
        
        ctx.fillStyle = 'rgba(0,0,0,0.3)';
        ctx.fillRect(0, 330, 800, 120);
        
        ctx.fillStyle = '#FFFFFF';
        ctx.font = '24px Cairo, system-ui, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('تم الإبلاغ عن هذه السيارة من قِبل المجتمع', 400, 370);
        ctx.font = '20px Cairo, system-ui, sans-serif';
        ctx.fillText('This vehicle has been reported by the community', 400, 405);
        
        ctx.fillStyle = 'rgba(255,255,255,0.5)';
        ctx.font = '14px Cairo, system-ui, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('أمان • Aman Safety Network', 400, 440);
        
        const now = new Date();
        ctx.textAlign = 'right';
        ctx.fillText(now.toLocaleString(), 790, 440);
        
        canvas.toBlob(async (blob) => {
            if(!blob) return;
            const filename = `aman-warning-${plateText}.png`;
            
            if (navigator.share && navigator.canShare && navigator.canShare({ files: [new File([blob], filename, {type: 'image/png'})] })) {
                try {
                    await navigator.share({
                        files: [new File([blob], filename, {type: 'image/png'})],
                        title: 'Aman Warning: ' + plateText,
                        text: `Warning for plate ${plateText}\nCategory: ${category}\nGovernorate: ${governorate}`
                    });
                    return;
                } catch(e) {
                    console.log('Share error or cancelled', e);
                }
            }
            
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(a.href);
        }, 'image/png');
    } catch (err) {
        console.error('Canvas error:', err);
        alert('تعذّر إنشاء البطاقة | Could not generate warning card');
    }
};
