document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded. Initializing app.');

    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const inputString = document.getElementById('input-string');
    const validateButton = document.getElementById('validate-button');
    const validationOutput = document.getElementById('validation-output');
    const languageSelect = document.getElementById('language-select'); // Lấy element ngôn ngữ

    if (!themeToggle || !inputString || !validateButton || !validationOutput || !languageSelect) {
        console.error("One or more required DOM elements not found. Check HTML IDs.");
        return;
    }

    // --- Chức năng chuyển đổi chế độ sáng/tối ---
    console.log('Setting up theme toggle.');
    themeToggle.addEventListener('click', () => {
        body.classList.toggle('dark-mode');
        if (body.classList.contains('dark-mode')) {
            localStorage.setItem('theme', 'dark');
            console.log('Switched to dark mode.');
        } else {
            localStorage.setItem('theme', 'light');
            console.log('Switched to light mode.');
        }
    });

    if (localStorage.getItem('theme') === 'dark') {
        body.classList.add('dark-mode');
        console.log('Loaded dark mode from localStorage.');
    } else {
        console.log('Loaded light mode (default or from localStorage).');
    }

    // --- Lưu và tải lựa chọn ngôn ngữ ---
    const savedLanguage = localStorage.getItem('validationLanguage');
    if (savedLanguage) {
        languageSelect.value = savedLanguage;
        console.log('Loaded language from localStorage:', savedLanguage);
    } else {
        // Mặc định là Japanese (ja) như trong option HTML ban đầu
        localStorage.setItem('validationLanguage', languageSelect.value);
        console.log('Default language set to:', languageSelect.value);
    }

    languageSelect.addEventListener('change', () => {
        localStorage.setItem('validationLanguage', languageSelect.value);
        console.log('Language changed to:', languageSelect.value);
        // Có thể tự động chạy validation lại khi đổi ngôn ngữ nếu muốn
        // if (inputString.value.trim() !== '') {
        //     runValidation();
        // }
    });

    // --- Chức năng tự động xác nhận định dạng JSON/XML cơ bản ---
    function isValidJson(str) {
        try {
            JSON.parse(str);
            return true;
        } catch (e) {
            return false;
        }
    }

    function isValidXml(str) {
        try {
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(str, "application/xml");
            return xmlDoc.getElementsByTagName("parsererror").length === 0 && xmlDoc.childNodes.length > 0;
        } catch (e) {
            return false;
        }
    }

    // --- Hàm chạy validation (gọi API backend) ---
    async function runValidation() {
        console.log('Validation button clicked. Starting validation process.');
        validationOutput.innerHTML = '';
        const inputText = inputString.value.trim();
        const selectedLanguage = languageSelect.value; // Lấy ngôn ngữ đã chọn

        if (inputText === '') {
            validationOutput.innerHTML = '<p class="info">Vui lòng nhập chuỗi để kiểm tra.</p>';
            console.log('Input text is empty.');
            return;
        }

        let inputFormat = 'unknown';
        let detectedMessage = '';

        if (isValidJson(inputText)) {
            inputFormat = 'json';
            detectedMessage = 'Định dạng tự động xác nhận: JSON.';
        } else if (isValidXml(inputText)) {
            inputFormat = 'xml';
            detectedMessage = 'Định dạng tự động xác nhận: XML (kiểm tra cú pháp cơ bản).';
        } else {
            validationOutput.innerHTML += '<p class="error">Lỗi: Chuỗi không phải là JSON hoặc XML hợp lệ. Vui lòng kiểm tra lại cú pháp.</p>';
            console.warn('Input text is neither valid JSON nor XML.');
            return;
        }

        validationOutput.innerHTML += `<p class="info">${detectedMessage}</p>`;
        validationOutput.innerHTML += `<p class="info">Đang gửi dữ liệu đến máy chủ để xác thực FHIR JP-CLINS (Ngôn ngữ: ${selectedLanguage})...</p>`;
        validateButton.disabled = true;

        try {
            console.log('Sending request to backend API /api/validate...');
            const response = await fetch('/api/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    data: inputText,
                    format: inputFormat,
                    language: selectedLanguage // Gửi ngôn ngữ đã chọn
                })
            });

            console.log('Received response from backend.', response);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: 'Không thể phân tích lỗi từ máy chủ.' }));
                throw new Error(errorData.message || `Lỗi từ máy chủ: ${response.status} ${response.statusText}`);
            }

            const result = await response.json();

            console.log('Validation result:', result);

            validationOutput.innerHTML = ''; // Xóa các thông báo loading/detected

            if (result && Array.isArray(result.messages)) {
                if (result.messages.length === 0) { // Nếu backend không trả về lỗi/cảnh báo chi tiết
                    validationOutput.innerHTML += '<p class="info">Validation thành công: Không tìm thấy lỗi FHIR JP-CLINS.</p>';
                } else {
                    result.messages.forEach(msg => {
                        const p = document.createElement('p');
                        p.textContent = msg.text;
                        if (msg.type === 'error') {
                            p.classList.add('error');
                        } else if (msg.type === 'warning') {
                            p.classList.add('warning');
                        } else {
                            p.classList.add('info');
                        }
                        validationOutput.appendChild(p);
                    });
                }
            } else {
                validationOutput.innerHTML += '<p class="error">Lỗi: Không nhận được phản hồi kết quả validation hợp lệ từ máy chủ.</p>';
            }

        } catch (error) {
            validationOutput.innerHTML = `<p class="error">Lỗi trong quá trình xác thực: ${error.message}. Vui lòng kiểm tra kết nối tới Backend và Console để biết thêm chi tiết.</p>`;
            console.error('Validation API error:', error);
        } finally {
            validateButton.disabled = false;
            console.log('Validation process finished.');
        }
    }

    console.log('Attaching event listener to validate button.');
    validateButton.addEventListener('click', runValidation);
});