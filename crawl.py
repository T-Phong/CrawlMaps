from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import pandas as pd

def crawl_location(url,ten,num_of_reviews):
    # --- 1. CẤU HÌNH ---
    options = Options()
    # Cấu hình ngôn ngữ Tiếng Việt để tìm element cho chuẩn
    options.add_argument("--lang=vi") 
    # options.add_argument("headless") # Bỏ comment nếu muốn chạy ẩn

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    # URL mục tiêu
    #url = "https://www.google.com/maps/place/GoGi+House/data=!4m7!3m6!1s0x31752fd65664ea59:0xe6a525b021e078f!8m2!3d10.7733531!4d106.7038615!16s%2Fg%2F11j4qh4r8h!19sChIJWepkVtYvdTERjwceAltSag4?authuser=0&hl=vi&rclk=1"  # Thay URL thực tế của bạn vào đây

    try:
        # --- 2. MỞ TRANG & ANTI-BOT ---
        print("[INFO] Đang mở trang Google Maps...")
        driver.get(url)
        
        # Thao tác chuột giả lập
        action = ActionChains(driver)
        try:
            print("[INFO] Đang di chuyển chuột giả lập...")
            action.move_by_offset(50, 50).perform()
            time.sleep(2)
            
            print("[INFO] Đang tải lại trang (F5) để tránh lỗi giao diện...")
            driver.refresh()
            time.sleep(5) # Chờ tải lại hoàn tất
        except Exception as e:
            print(f"[WARN] Lỗi thao tác chuột/refresh: {e}")

        # --- 3. MỞ TAB ĐÁNH GIÁ (REVIEWS) ---
        print("[INFO] Đang tìm cách mở danh sách đánh giá...")
        try:
            # Thử tìm nút "Bài đánh giá" hoặc "Reviews"
            review_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@aria-label, 'Bài đánh giá') or contains(@aria-label, 'Reviews')]")
            ))
            review_btn.click()
            print("[INFO] Đã click tab 'Bài đánh giá'.")
        except:
            # Nếu không thấy tab, click vào dòng số lượng đánh giá (Ví dụ: "100 đánh giá")
            print("[INFO] Không thấy tab riêng, đang thử click vào số lượng đánh giá...")
            try:
                rating_count_btn = driver.find_element(By.CSS_SELECTOR, "button[jsaction*='pane.rating.more'], div.F7nice button")
                rating_count_btn.click()
                print("[INFO] Đã click vào số lượng đánh giá thành công.")
            except:
                print("[ERROR] Không thể mở phần đánh giá.")

        time.sleep(3) # Chờ load

        # --- 4. CHỨC NĂNG MỚI: CHỌN SẮP XẾP THẤP NHẤT ---
        # --- 4. CHỨC NĂNG MỚI: CHỌN SẮP XẾP THẤP NHẤT (ĐÃ SỬA LỖI) ---
        try:
            print("[INFO] Đang tìm nút Sắp xếp...")
            
            # 1. Click nút mở menu Sắp xếp
            # Tìm nút menu
            sort_button = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//button[contains(@aria-label, 'Phù hợp nhất') or .//span[contains(text(), 'Phù hợp nhất')]]")
            ))
            # Dùng JS Click cho chắc chắn
            driver.execute_script("arguments[0].click();", sort_button)
            time.sleep(1) # Chờ menu xổ xuống

            # 2. Chọn tùy chọn "Thấp nhất" (Lowest)
            print("[INFO] Đang chọn 'Thấp nhất'...")
            
            # Tìm phần tử menu item chứa chữ "Thấp nhất" hoặc "Lowest"
            # Chúng ta tìm thẻ cha có role='menuitemradio' để click chính xác vào ô chọn
            lowest_option = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[@role='menuitemradio' and (.//div[contains(text(), 'thấp nhất')] or .//div[contains(text(), 'Lowest')])]"))
            )
            
            # --- KHẮC PHỤC LỖI INTERCEPTED TẠI ĐÂY ---
            # Thay vì dùng lowest_option.click(), ta dùng lệnh javascript bên dưới:
            driver.execute_script("arguments[0].click();", lowest_option)
            
            print("[INFO] Đã click chọn 'Thấp nhất' bằng JavaScript.")
            time.sleep(4) # BẮT BUỘC CHỜ để danh sách tải lại thứ tự mới
            
        except Exception as e:
            print(f"[WARN] Không thể sắp xếp (Lỗi: {e}) -> Sẽ lấy theo thứ tự mặc định.")

        # --- 5. CUỘN VÀ LẤY DỮ LIỆU ---
        reviews_data = []
        seen_reviews = set()
        scroll_attempt = 0
        max_scroll_attempts = 50 # Giới hạn số lần cuộn
        target_count = 50
        if num_of_reviews > 200:
            target_count = 75 # Số lượng muốn lấy
        elif num_of_reviews > 500:
            target_count = 100
        elif num_of_reviews > 1000:
            target_count = 150
        else:
            target_count = 50
        print("[INFO] Bắt đầu cuộn trang...")

        # Tìm khung chứa thanh cuộn (Quan trọng)
        try:
            scrollable_div = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div[role="main"] div[tabindex="-1"]')
            ))
        except:
            print("[ERROR] Không tìm thấy khung cuộn review.")
            driver.quit()
            exit()

        while len(reviews_data) < target_count and scroll_attempt < max_scroll_attempts:
            
            # Thực hiện cuộn xuống cuối div
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            time.sleep(2) # Chờ tải thêm review mới

            # Lấy tất cả các thẻ review hiện có
            review_containers = driver.find_elements(By.CSS_SELECTOR, 'div.jftiEf')
            
            for container in review_containers:
                # Chỉ xử lý các review mới tải để tối ưu tốc độ (tùy chọn)
                # Ở đây ta duyệt lại để chắc chắn không sót
                
                try:
                    # 1. Lấy tên
                    try:
                        username = container.find_element(By.CLASS_NAME, 'd4r55').text.strip()
                    except:
                        username = 'Unknown'

                    # 2. Lấy nội dung
                    try:
                        review_text = container.find_element(By.CLASS_NAME, 'wiI7pd').text.strip()
                    except:
                        review_text = '' # Nhiều người chỉ chấm sao mà không viết chữ
                    
                    if not review_text or len(review_text) < 5:
                        continue # Bỏ qua nếu không có nội dung hoac noi dung qua ngan

                    # laasy nội dung đầy đủ nếu có nút "Đọc thêm"
                    try:
                        more = container.find_element(By.CLASS_NAME, 'w8nwRe')
                        driver.execute_script("arguments[0].click();", more)
                        time.sleep(1)
                        review_text = container.find_element(By.CLASS_NAME, 'wiI7pd').text.strip()
                    except:
                        pass        

                    # 3. Lấy số sao
                    try:
                        rating_element = container.find_element(By.CLASS_NAME, 'kvMYJc')
                        rating_raw = rating_element.get_attribute('aria-label') # vd: "2 sao"
                        # Lấy số đầu tiên trong chuỗi
                        rating = rating_raw.split()[0].replace(',', '.') 
                    except:
                        rating = 'N/A'

                    # Kiểm tra trùng lặp (Dựa trên tên và nội dung)
                    unique_key = (username, review_text)
                    if unique_key not in seen_reviews:
                        seen_reviews.add(unique_key)
                        reviews_data.append({
                            'user': username,
                            'rating': rating,
                            'review': review_text
                        })
                except Exception as e:
                    continue # Bỏ qua review lỗi

            print(f"[INFO] Đã thu thập: {len(reviews_data)} đánh giá...")
            
            if len(reviews_data) >= target_count:
                print("[INFO] Đã đủ số lượng yêu cầu.")
                break
                
            scroll_attempt += 1

        # --- 6. XUẤT KẾT QUẢ ---
        # print("\n=== KẾT QUẢ ===")
        # for i, item in enumerate(reviews_data[:target_count], 1):
        #     print(f"{i}. [{item['rating']} sao] {item['user']}: {item['review'][:50]}...")

        # Lưu file Excel (Nếu cần)
        df = pd.DataFrame(reviews_data)
        df.to_excel('danh_gia_thap_nhat_'+ten+'.xlsx', index=False)
        print("[INFO] Đã lưu file Excel.")

    except Exception as e:
        print(f"[ERROR] Lỗi chương trình: {e}")

    finally:
        print("[INFO] Đóng trình duyệt.")
        driver.quit()