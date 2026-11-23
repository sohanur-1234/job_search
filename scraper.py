import html
import io
import json
import os
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from google import genai
from google.genai import types
import urllib3

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

SEEN_FILE = "seen_links.json"
OPPORTUNITIES_FILE = "opportunities.json"
SUBSCRIBERS_FILE = "subscribers.json"

CANDIDATE_PROFILE = """
- Education: B.Sc. in Computer Science & Engineering (CSE), Islamic University, Bangladesh.
- Research Interests: Deep Learning, Biomedical Signal Processing (EEG seizure detection), Computer Vision, 3D Vision, AI/ML.
- Technical Stack: Python, PyTorch, TensorFlow/Keras, Scikit-learn, MNE-Python, NumPy, Pandas, C++.
- Goal: Paid or funded Research Assistant (RA) / Junior Research Assistant position under a professor or research lab.
"""

TARGET_URLS = [
    {"name": "BRACU Career", "url": "https://www.bracu.ac.bd/about/career-at-bracu"},
    {"name": "NSU Jobs", "url": "https://www.northsouth.edu/jobs-at-nsu.html"},
    {"name": "UIU Career", "url": "https://www.uiu.ac.bd/career/"},
    {"name": "UIU AIMS Lab", "url": "https://aims.uiu.ac.bd/"},
    {"name": "UIU CAIR", "url": "https://cair.uiu.ac.bd/"},
    {"name": "IUB Career", "url": "https://iub.edu.bd/career"},
    {"name": "IUB CCDS Lab", "url": "https://ccds.ai/"},
    {"name": "AIUB Career", "url": "https://www.aiub.edu/career"},
    {"name": "EWU Career", "url": "https://www.ewubd.edu/career"},
    {"name": "Aust Career", "url": "https://www.aust.edu/career"},
    {"name": "DIU Career", "url": "https://daffodilvarsity.edu.bd/career"},
    {"name": "ULAB Career", "url": "https://ulab.edu.bd/career"},
    {"name": "UAP Career", "url": "https://www.uap-bd.edu/career.php"},
    {"name": "BUET RISE", "url": "https://rise.buet.ac.bd/"},
    {"name": "BUET Notice", "url": "https://www.buet.ac.bd/web/#/notices"},
    {"name": "DU Jobs & Notices", "url": "https://www.du.ac.bd/notices"},
    {"name": "SUST Career", "url": "https://www.sust.edu/career"},
    {"name": "KUET Career", "url": "https://www.kuet.ac.bd/career"},
    {"name": "RUET Career", "url": "https://www.ruet.ac.bd/career"},
    {"name": "CUET Career", "url": "https://www.cuet.ac.bd/career"},
    {"name": "IUT Career", "url": "https://www.iutoic-dhaka.edu/career"},
    {"name": "JU Notice", "url": "https://juniv.edu/discussion"},
    {"name": "RU Notice", "url": "https://www.ru.ac.bd/notice/"},
    {"name": "CU Notice", "url": "https://cu.ac.bd/notice/"},
    {"name": "KU Notice", "url": "https://ku.ac.bd/notices"},
    {"name": "IU Notice", "url": "https://www.iu.ac.bd/index.php/site/notice"},
    {"name": "BUP Career", "url": "https://bup.edu.bd/careers"},
    {"name": "MIST Notice", "url": "https://mist.ac.bd/notice"},
    {"name": "icddr,b Career", "url": "https://career.icddrb.org/"},
    {"name": "UGC Notices", "url": "http://www.ugc.gov.bd/site/view/notices"},
    {"name": "ICT Division", "url": "https://ictd.gov.bd/site/view/notices"},
    {"name": "BCC Notices", "url": "https://bcc.gov.bd/site/view/notices"},
    {"name": "BIDS Career", "url": "https://bids.org.bd/page/career"},
    {"name": "BIGD Career", "url": "https://bigd.bracu.ac.bd/careers/"},
    {"name": "BCSIR Notices", "url": "https://bcsir.gov.bd/site/view/notices"},
    # Worldwide & International Research Boards
    {"name": "Cambridge Research Jobs (UK)", "url": "https://www.jobs.cam.ac.uk/research/"},
    {"name": "Imperial College Research (UK)", "url": "https://www.imperial.ac.uk/jobs/"},
    {"name": "NUS Singapore Research", "url": "https://careers.nus.edu.sg/search/?createNewAlert=false&q=Research+Assistant"},
    {"name": "TUM Germany Academic Jobs", "url": "https://portal.mytum.de/jobs/wissenschaftler/"},
    {"name": "EuroScienceJobs RA (Europe)", "url": "https://www.eurosciencejobs.com/jobs/research_assistant"},
    {"name": "Predoc.org Global Opportunities", "url": "https://predoc.org/opportunities"},
    {"name": "KAUST Research Jobs (Saudi Arabia)", "url": "https://www.kaust.edu.sa/en/about/working-at-kaust"},
    {"name": "HigherEdJobs Global Research", "url": "https://www.higheredjobs.com/search/advanced_action.cfm?JobCat=24"},
    # Japan Research Hubs & Top Universities
    {"name": "JREC-IN Japan (National Research Portal)", "url": "https://jrecin.jst.go.jp/seek/SeekTop?ln=1"},
    {"name": "RIKEN Research Institute (Japan)", "url": "https://www.riken.jp/en/careers/"},
    {"name": "University of Tokyo Jobs (Japan)", "url": "https://www.u-tokyo.ac.jp/en/about/jobs.html"},
    {"name": "Kyoto University Employment (Japan)", "url": "https://www.kyoto-u.ac.jp/en/about/employment"},
    {"name": "OIST Research Careers (Japan)", "url": "https://www.oist.jp/careers"},
    {"name": "NII National Institute of Informatics (Japan)", "url": "https://www.nii.ac.jp/en/about/recruit/"},
    # South Korea Research Hubs & Top Universities
    {"name": "KAIST Recruitment (South Korea)", "url": "https://news.kaist.ac.kr/newsen/html/news/?skey=category&sval=RECRUITMENT"},
    {"name": "Seoul National University Notices (South Korea)", "url": "https://www.snu.ac.kr/snunow/notice/genernal"},
]

PREFILTER_KEYWORDS = [
    "research assistant",
    "junior research",
    "research associate",
    "research fellow",
    "graduate research",
    "predoc",
    "pre-doc",
    "project researcher",
    "special researcher",
    "student researcher",
    "laboratory assistant",
    "lab researcher",
    "machine learning",
    "deep learning",
    "artificial intelligence",
    "data science",
    "biomedical",
    "computer vision",
    "visiting researcher",
    "grant",
    "ra ",
]

LINKEDIN_QUERIES = [
    # Global / Worldwide RA searches
    'site:linkedin.com/posts ("looking for RA" OR "hiring Research Assistant" OR "Research Assistant position") ("Machine Learning" OR "Deep Learning" OR "Computer Vision" OR "AI")',
    'site:linkedin.com/posts ("Graduate Research Assistant" OR "Pre-doc" OR "Visiting Researcher") ("Deep Learning" OR "Machine Learning" OR "Biomedical")',
    'site:linkedin.com/posts ("Research Assistant" OR "RA vacancy" OR "funded RA") ("USA" OR "Canada" OR "Germany" OR "UK" OR "Europe" OR "Singapore" OR "Australia")',
    'site:linkedin.com/jobs "Research Assistant" ("Machine Learning" OR "Deep Learning" OR "Computer Science")',
    # Japan & South Korea focused searches
    'site:linkedin.com/posts ("Research Assistant" OR "Graduate Research Assistant" OR "Intern" OR "RA") ("Japan" OR "Tokyo" OR "Kyoto" OR "RIKEN" OR "OIST" OR "JREC-IN")',
    'site:linkedin.com/posts ("Research Assistant" OR "Graduate Research Assistant" OR "Lab" OR "RA") ("South Korea" OR "Korea" OR "KAIST" OR "SNU" OR "POSTECH")',
    # Bangladesh specific
    'site:linkedin.com/posts "Research Assistant" ("BUET" OR "NSU" OR "BRACU" OR "UIU" OR "Dhaka" OR "Bangladesh")',
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def sync_subscribers():
    """Checks incoming /start or /stop messages and updates subscribers.json."""
    subscribers = set(load_json(SUBSCRIBERS_FILE, []))
    if CHAT_ID:
        try:
            subscribers.add(int(CHAT_ID))
        except (ValueError, TypeError):
            subscribers.add(CHAT_ID)

    if not BOT_TOKEN:
        return list(subscribers)

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        res = requests.get(url, timeout=15).json()
        if not res.get("ok") and res.get("error_code") == 409:
            requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook", timeout=10)
            res = requests.get(url, timeout=15).json()
        updates = res.get("result", [])
        max_update_id = None

        for upd in updates:
            max_update_id = upd["update_id"]
            msg = upd.get("message", {})
            chat_id = msg.get("chat", {}).get("id")
            text = (msg.get("text") or "").strip().lower()

            if not chat_id:
                continue

            if text.startswith("/stop"):
                subscribers.discard(chat_id)
                send_to_chat(chat_id, "🛑 Unsubscribed. Send /start anytime to rejoin.")
            else:
                if chat_id not in subscribers:
                    subscribers.add(chat_id)
                    send_to_chat(chat_id, "✅ Subscribed! You will now receive RA & research alerts.")

        # Acknowledge processed updates so Telegram clears them from the queue
        if max_update_id is not None:
            requests.get(url, params={"offset": max_update_id + 1}, timeout=10)
    except Exception as e:
        print(f"Subscriber sync error: {e}")

    subscriber_list = sorted(list(subscribers))
    save_json(SUBSCRIBERS_FILE, subscriber_list)
    return subscriber_list


def send_to_chat(chat_id, text):
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text[:4000],
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        res = requests.post(api_url, json=payload, timeout=15)
        # Remove user if they blocked the bot (HTTP 403)
        if res.status_code == 403:
            subs = set(load_json(SUBSCRIBERS_FILE, []))
            subs.discard(chat_id)
            save_json(SUBSCRIBERS_FILE, sorted(list(subs)))
    except Exception as e:
        print(f"Telegram send error for {chat_id}: {e}")


def broadcast_message(text, subscribers):
    if not BOT_TOKEN:
        return
    for chat_id in subscribers:
        send_to_chat(chat_id, text)


def extract_link_details(url):
    """Fetches text from a circular page or extracts text from a PDF link."""
    try:
        res = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        res.raise_for_status()
        content_type = res.headers.get("Content-Type", "").lower()

        if url.lower().endswith(".pdf") or "application/pdf" in content_type:
            reader = PdfReader(io.BytesIO(res.content))
            text = ""
            for page in reader.pages[:2]:
                text += (page.extract_text() or "") + "\n"
            return " ".join(text.split())[:3000]

        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return " ".join(soup.get_text().split())[:3000]
    except Exception:
        return ""


def evaluate_with_free_llm(source, title, link, body_text):
    """Uses free Gemini API to filter noise, extract metadata, and draft a cold email."""
    if not GEMINI_API_KEY:
        return {
            "is_relevant": True,
            "score": 7,
            "deadline": "Check link",
            "contact_email": "Check link",
            "summary": title,
            "cold_email": "",
        }

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = f"""
You are an academic career assistant. Analyze this notice/post for the candidate below.

CANDIDATE PROFILE:
{CANDIDATE_PROFILE}

NOTICE DETAILS:
Source: {source}
Title: {title}
Link: {link}
Extracted Content: {body_text if body_text else "No extra page text available."}

Return ONLY valid JSON with these exact keys:
{{
  "is_relevant": true or false (true ONLY if it is an actual Research Assistant, Research Associate, Research Fellow, or funded research project recruitment for BSc/CSE/AI/ML students; false for exam routines, seminars, admissions, or unrelated admin jobs),
  "score": integer 1 to 10 (how well it matches the candidate's CSE/AI/Deep Learning/EEG background),
  "deadline": "extracted deadline or 'Not specified'",
  "contact_email": "extracted email address or 'Apply via link'",
  "summary": "2-sentence concise summary of role, topic, and eligibility",
  "cold_email": "If score >= 7, write a crisp, professional 120-word cold email tailored to this post from MD Sohanur Rahman Sohan highlighting Python, PyTorch/TensorFlow, and Deep Learning/EEG experience. Otherwise empty string."
}}
"""
    try:
        response = None
        for model_name in ["gemini-3-flash-preview", "gemini-3.8-flash", "gemini-flash-latest"]:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
                if response and response.text:
                    break
            except Exception:
                continue
        if not response or not response.text:
            raise RuntimeError("Gemini model generation failed")
        return json.loads(response.text)
    except Exception as e:
        print(f"LLM evaluation error: {e}")
        return {
            "is_relevant": True,
            "score": 7,
            "deadline": "Check link",
            "contact_email": "Check link",
            "summary": title,
            "cold_email": "",
        }


def scrape_site(source):
    found_items = []
    try:
        response = requests.get(source["url"], headers=HEADERS, timeout=20, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for a_tag in soup.find_all("a", href=True):
            title = " ".join(a_tag.get_text().split())
            href = a_tag["href"]
            if len(title) < 8:
                continue

            combined = f"{title} {href}".lower()
            if any(kw in combined for kw in PREFILTER_KEYWORDS):
                full_link = urljoin(source["url"], href)
                found_items.append(
                    {"source": source["name"], "title": title, "link": full_link}
                )
    except Exception as e:
        print(f"Error scraping {source['name']}: {e}")
    return found_items


def search_google_linkedin():
    found_items = []
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return found_items

    endpoint = "https://www.googleapis.com/customsearch/v1"
    for query in LINKEDIN_QUERIES:
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "q": query,
            "dateRestrict": "d7",
            "num": 10,
        }
        try:
            res = requests.get(endpoint, params=params, timeout=15)
            res.raise_for_status()
            for item in res.json().get("items", []):
                link = item.get("link", "")
                if link:
                    found_items.append(
                        {
                            "source": "LinkedIn (Google Search)",
                            "title": f"{item.get('title', '')} — {item.get('snippet', '')}",
                            "link": link,
                        }
                    )
        except Exception as e:
            print(f"Google Search error: {e}")
    return found_items


def main():
    subscribers = sync_subscribers()
    seen_links = set(load_json(SEEN_FILE, []))
    opportunities = load_json(OPPORTUNITIES_FILE, [])
    candidates = []

    for source in TARGET_URLS:
        for item in scrape_site(source):
            if item["link"] not in seen_links:
                seen_links.add(item["link"])
                candidates.append(item)

    for item in search_google_linkedin():
        if item["link"] not in seen_links:
            seen_links.add(item["link"])
            candidates.append(item)

    sent_count = 0
    for item in candidates:
        body_text = extract_link_details(item["link"])
        analysis = evaluate_with_free_llm(
            item["source"], item["title"], item["link"], body_text
        )

        if not analysis.get("is_relevant") or analysis.get("score", 0) < 6:
            continue

        record = {
            "source": item["source"],
            "title": item["title"],
            "link": item["link"],
            "score": analysis.get("score"),
            "deadline": analysis.get("deadline"),
            "contact_email": analysis.get("contact_email"),
            "summary": analysis.get("summary"),
        }
        opportunities.insert(0, record)

        msg = (
            f"🎯 <b>RA Match ({record['score']}/10) — {html.escape(record['source'])}</b>\n\n"
            f"📌 <b>Title:</b> {html.escape(record['title'][:200])}\n"
            f"📝 <b>Summary:</b> {html.escape(record['summary'])}\n"
            f"⏳ <b>Deadline:</b> {html.escape(record['deadline'])}\n"
            f"📧 <b>Contact:</b> {html.escape(record['contact_email'])}\n"
            f"🔗 <b>Link:</b> {html.escape(record['link'])}"
        )
        broadcast_message(msg, subscribers)

        if analysis.get("cold_email"):
            email_msg = (
                f"✉️ <b>Ready-to-Send Cold Email Draft:</b>\n\n"
                f"<pre>{html.escape(analysis['cold_email'])}</pre>"
            )
            broadcast_message(email_msg, subscribers)

        sent_count += 1

    save_json(SEEN_FILE, sorted(list(seen_links)))
    save_json(OPPORTUNITIES_FILE, opportunities[:200])
    print(f"Processed {len(candidates)} new links; sent {sent_count} relevant alerts to {len(subscribers)} subscribers.")


if __name__ == "__main__":
    main()
