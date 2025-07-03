import os
import subprocess
import json
import logging
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

backend_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(os.path.dirname(backend_dir), 'frontend')

app = Flask(__name__,
            static_folder=frontend_dir,
            static_url_path='/')

CORS(app)

APP_ROOT = "/app"
VALIDATOR_DATA_DIR = os.path.join(APP_ROOT, "validator-data")
VALIDATOR_JAR = os.path.join(VALIDATOR_DATA_DIR, "validator_cli.jar")

TARGETS_DIR = os.path.join(APP_ROOT, "targets")
os.makedirs(TARGETS_DIR, exist_ok=True)

PKG_CLINS_DIR = os.path.join(VALIDATOR_DATA_DIR, "packages")
os.makedirs(PKG_CLINS_DIR, exist_ok=True)

JP_CORE_IG = os.path.join(PKG_CLINS_DIR, "jp-core.r4-1.1.2-clins.tgz")
JPFHIR_TERMINOLOGY_IG = os.path.join(PKG_CLINS_DIR, "jpfhir-terminology.r4-1.3.0.tgz")
JP_ECSLINS_IG = os.path.join(PKG_CLINS_DIR, "jp-eCSCLINS.r4-1.10.0.tgz")


@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/validate', methods=['POST'])
def validate_fhir_data():
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({"message": "Dữ liệu JSON không hợp lệ.", "messages": [{"type": "error", "text": "Dữ liệu đầu vào trống hoặc không đúng định dạng."}]}), 400

    input_data = data['data']
    input_format = data.get('format', 'json')
    req_language = data.get('language', 'en') # Mặc định tiếng Anh để tránh lỗi encoding

    if req_language == 'en':
        locale_param = 'en-US'
    elif req_language == 'vi':
        # Vẫn dùng tiếng Anh cho validator nếu chọn tiếng Việt
        locale_param = 'en-US'
        language_param = 'en'
    else: # Mặc định là Japanese
        locale_param = 'ja-JP'
    language_param = req_language if req_language in ['ja', 'en'] else 'en'


    temp_json_file = os.path.join(TARGETS_DIR, "input_data.json")

    try:
        with open(temp_json_file, 'w', encoding='utf-8') as f:
            if input_format == 'json':
                try:
                    json_object = json.loads(input_data)
                    f.write(json.dumps(json_object, indent=2, ensure_ascii=False))
                except json.JSONDecodeError:
                    f.write(input_data)
            else:
                f.write(input_data)

        logging.info(f"Đã lưu dữ liệu tạm thời vào: {temp_json_file}")

        command = [
            "java",
            # Thêm "-Dfile.encoding=UTF-8" để khắc phục cảnh báo encoding của Java
            "-Dfile.encoding=UTF-8",
            "-jar", VALIDATOR_JAR,
            temp_json_file,
            "-version", "4.0.1",
            "-language", language_param,
            "-locale", locale_param,
            "-want-invariants-in-messages",
            "-no-extensible-binding-warnings",
            "-display-issues-are-warnings",
            "-level", "warnings",
            "-best-practice", "ignore",
            "-tx", "n/a",
            "-ig", JP_CORE_IG,
            "-ig", JPFHIR_TERMINOLOGY_IG,
            "-ig", JP_ECSLINS_IG
        ]

        logging.info(f"Lệnh validator sẽ chạy: {' '.join(command)}")

        process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', cwd=APP_ROOT)
        raw_stdout = process.stdout.strip()
        raw_stderr = process.stderr.strip()

        logging.info(f"Validator stdout:\n{raw_stdout}")
        if raw_stderr:
            logging.error(f"Validator stderr:\n{raw_stderr}")

        validation_messages = []
        overall_status_line = ""
        
        # Regex để bắt các loại thông báo cụ thể.
        # Sử dụng re.IGNORECASE để bắt "Error", "ERROR"
        # Bắt đầu dòng có thể có bất kỳ ký tự không phải chữ/số nào (non-word, non-space) hoặc khoảng trắng.
        # Sau đó bắt từ khóa lỗi/cảnh báo và nội dung còn lại của dòng.
        error_pattern = re.compile(r"^\s*(?:[\W\s]*)(?:Error|Lỗi|FAILURE|FAIL)\s*@?\s*(.*)", re.IGNORECASE)
        warning_pattern = re.compile(r"^\s*(?:[\W\s]*)(?:Warning|Cảnh báo)\s*@?\s*(.*)", re.IGNORECASE)
        info_pattern = re.compile(r"^\s*(?:[\W\s]*)(?:Information|Note|Thông tin|Ghi chú|Validating|Loading|Done\. Times:|Package Summary:|Java:|Paths:|Params:|Locale:|Jurisdiction:|Terminolog|Get set\.\.\.).*", re.IGNORECASE)

        for line in raw_stdout.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            error_match = error_pattern.match(line)
            warning_match = warning_pattern.match(line)
            info_match = info_pattern.match(line)

            if error_match:
                content = error_match.group(1).strip()
                if "errors," in content and "warnings," in content and "notes" in content: # Đây là dòng summary *FAILURE*
                    overall_status_line = line
                    validation_messages.append({"type": "error", "text": "Validation thất bại: " + content})
                else:
                    validation_messages.append({"type": "error", "text": "Error: " + content})
            elif warning_match:
                content = warning_match.group(1).strip()
                if "errors," in content and "warnings," in content and "notes" in content: # Đây là dòng summary Success with Warnings
                    overall_status_line = line
                    validation_messages.append({"type": "warning", "text": "Validation có cảnh báo: " + content})
                else:
                    validation_messages.append({"type": "warning", "text": "Warning: " + content})
            elif line.startswith("Success:"): # Bắt dòng success summary
                overall_status_line = line
                if "0 errors" in line and "0 warnings" in line:
                    # Nếu là success hoàn toàn không có lỗi/cảnh báo, chúng ta sẽ thêm thông báo tổng sau.
                    pass 
                else: # Success nhưng có lỗi hoặc cảnh báo (sẽ được bắt bởi các regex khác)
                    validation_messages.append({"type": "warning", "text": "Validation hoàn thành với các cảnh báo hoặc lỗi (kiểm tra chi tiết bên dưới): " + line})
            elif info_match:
                # Bỏ qua các dòng log nội bộ của validator quá chi tiết
                if not any(keyword in line for keyword in ["Loading", "Load ", "Installing", "Fetching", "done", "Done. Times", "Memory", "Java:", "Paths:", "Params:", "Locale:", "Jurisdiction:", "Terminology Cache", "Get set...", "Validating"]):
                    validation_messages.append({"type": "info", "text": "Info: " + line})
            else:
                # Nếu một dòng không khớp với bất kỳ regex nào, có thể nó là một phần của thông báo dài hơn
                # hoặc một loại thông báo mới. Chúng ta thêm nó dưới dạng info để không bỏ sót.
                validation_messages.append({"type": "info", "text": "Raw Output: " + line})

        # Xử lý các lỗi từ stderr (luôn là lỗi)
        if raw_stderr:
            for err_line in raw_stderr.split('\n'):
                err_line = err_line.strip()
                if err_line:
                    validation_messages.append({"type": "error", "text": f"Lỗi từ Validator (stderr): {err_line}"})
        
        # Quyết định trạng thái tổng thể dựa vào overall_status_line hoặc các lỗi/cảnh báo đã thu thập
        final_has_errors = any(msg['type'] == 'error' for msg in validation_messages)
        final_has_warnings = any(msg['type'] == 'warning' for msg in validation_messages)

        # Thêm thông báo tổng quan cuối cùng nếu danh sách rỗng hoặc chỉ chứa info
        if not final_has_errors and not final_has_warnings:
             if not any(msg['type'] == 'info' and msg['text'].startswith("Validation thành công") for msg in validation_messages):
                validation_messages.insert(0, {"type": "info", "text": "Validation thành công: Không tìm thấy lỗi FHIR JP-CLINS."})
        elif final_has_errors:
            # Nếu có lỗi, đảm bảo thông báo chung về lỗi được đưa lên đầu
            if not any(msg['text'].startswith("Validation thất bại:") for msg in validation_messages):
                validation_messages.insert(0, {"type": "error", "text": "Validation thất bại: Dữ liệu không tuân thủ các quy tắc FHIR JP-CLINS."})
        elif final_has_warnings:
            # Nếu chỉ có cảnh báo, đảm bảo thông báo chung về cảnh báo được đưa lên đầu
            if not any(msg['text'].startswith("Validation có cảnh báo:") for msg in validation_messages):
                validation_messages.insert(0, {"type": "warning", "text": "Validation có cảnh báo: Dữ liệu có thể cần điều chỉnh."})

        # Loại bỏ các thông báo trùng lặp hoặc quá chung chung nếu đã có thông báo chi tiết
        unique_messages = []
        seen_texts = set()
        for msg in validation_messages:
            if msg['text'] not in seen_texts:
                unique_messages.append(msg)
                seen_texts.add(msg['text'])
        
        # Sắp xếp để Error lên đầu, sau đó Warning, cuối cùng là Info
        unique_messages.sort(key=lambda x: {'error': 1, 'warning': 2, 'info': 3}.get(x['type'], 4))


        return jsonify({"messages": unique_messages})

    except Exception as e:
        logging.exception("Lỗi khi xử lý validation:")
        return jsonify({"message": f"Lỗi nội bộ máy chủ: {str(e)}", "messages": [{"type": "error", "text": f"Lỗi nội bộ máy chủ: {str(e)}"}]}), 500
    finally:
        if os.path.exists(temp_json_file):
            os.remove(temp_json_file)
            logging.info(f"Đã xóa file tạm thời: {temp_json_file}")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)