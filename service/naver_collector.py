# src/service/naver_collector.py
import requests

# 네이버 설정 (유저님의 키 유지)
CLIENT_ID = "0gtFqh3UWbQ0TJl_gW7u"
CLIENT_SECRET = "gsH8YkwdSk"

# 카테고리 & 필터 설정
CATEGORIES = ["한식", "양식", "일식", "중식"]
EXCLUSION_LIST = ["버거킹", "맥도날드", "스타벅스", "투썸플레이스", "이디야", "아웃백", "빕스", "서브웨이", "롯데리아"]


def fetch_real_image(query: str):
    """
    식당 이름으로 네이버 이미지 검색을 수행하여 진짜 사진 링크 1개를 가져옵니다.
    """
    url = "https://openapi.naver.com/v1/search/image"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    # 정확도를 높이기 위해 식당 이름 뒤에 '음식' 키워드를 추가하여 검색합니다.
    params = {"query": query + " 음식", "display": 1, "sort": "sim"}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        items = data.get("items", [])
        if items:
            return items[0]['link']  # 가장 유사한 첫 번째 이미지 링크 반환
    except Exception as e:
        print(f"🖼️ '{query}' 이미지 검색 에러: {e}")

    return ""  # 실패 시 빈 문자열 반환


def search_restaurants_by_location(location: str):
    """
    위치(예: 경복궁역)를 받아서 한/양/일/중식 Top 5를 뽑아 진짜 이미지와 함께 반환합니다.
    """
    url = "https://openapi.naver.com/v1/search/local.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }

    all_results = []
    print(f"🔍 '{location}' 진짜 맛집 검색 시작 (사진 포함)...")

    for category in CATEGORIES:
        # 검색어 조합 (예: 경복궁역 한식)
        query = f"{location} {category}"

        # '양식'인 경우 파스타로 검색어 변경 (유저님 꿀팁 적용)
        if category == "양식":
            query = f"{location} 파스타"

        params = {
            "query": query,
            "display": 5,  # 카테고리당 5개씩
            "sort": "comment"  # 리뷰(코멘트) 많은 순
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            items = data.get("items", [])

            for item in items:
                # HTML 태그 제거 (<b>태그 등)
                title = item['title'].replace("<b>", "").replace("</b>", "")
                address = item['roadAddress']

                # 1. 프랜차이즈 필터링 로직
                if any(brand in title for brand in EXCLUSION_LIST):
                    continue

                # 🚀 [수정 포인트] 여기서 진짜 이미지를 가져옵니다!
                # 식당 이름을 넘겨서 네이버 이미지 검색 결과 주소를 따옵니다.
                real_img_url = fetch_real_image(title)

                # 2. 결과 리스트에 추가 (딕셔너리 형태)
                restaurant_data = {
                    "title": title,
                    "address": address,
                    "category": category,
                    "naver_link": item['link'],
                    "img_url": real_img_url  # 👈 이제 진짜 이미지 주소가 들어갑니다!
                }
                all_results.append(restaurant_data)

        except Exception as e:
            print(f"❌ {category} 검색 중 에러: {e}")
            continue

    return all_results