
from crawl import crawl_location
from lstCraw import scrape_list


def main():
    print("Chương trình bắt đầu...")
    search_query = "quán ăn đường vạn kiếp" # Từ khóa tìm kiếm 
    results = scrape_list(search_query)
    for item in results:
        crawl_location(item['link'],item['Ten'],item['num_of_reviews'])
if __name__ == "__main__":
    main()