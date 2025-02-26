import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

# Configure Streamlit page
st.set_page_config(page_title="SEO Content Analyzer", layout="wide")
st.title("📊 SEO Content Analyzer")
st.markdown("Analyze website content while excluding unwanted sections like footers and navbars.")

# Create tabs
tab1, tab2, tab3 = st.tabs(["Single URL Analyzer", "Bulk Analyzer", "Keyword Tool"])

# Function to clean content and exclude unwanted sections
def get_clean_content(url):
    """Extract main content using Selenium and exclude unwanted sections."""
    try:
        # Configure Chrome options
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # Initialize WebDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        time.sleep(5)  # Wait longer for dynamic content to load
        
        # Parse page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        # Remove unwanted sections (footer, nav, etc.)
        for element in soup(['nav', 'header', 'footer', 'aside', 'script', 'style', 'form', 'button', 'div.footer', 'div.navbar']):
            element.decompose()

        # Focus on main content areas
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=lambda x: x and ('content' in x.lower() or 'main' in x.lower() or 'article' in x.lower()))
        
        if main_content:
            # Extract text only from visible elements (skip hidden text)
            content = []
            for element in main_content.find_all(text=True):
                if element.parent.name not in ['script', 'style']:  # Skip script and style tags
                    if not element.parent.has_attr('style') or ('display: none' not in element.parent['style'] and 'visibility: hidden' not in element.parent['style']):
                        content.append(element.strip())
            return ' '.join([text for text in content if text])
        return ''
    except Exception as e:
        st.error(f"Error processing {url}: {str(e)}")
        return ''

# Function to analyze content
def analyze_content(content, keywords):
    """Analyze content for word count, sentence count, and keyword density."""
    if not content:
        return 0, 0, []
    
    # Improved word counting (handles hyphenated words, apostrophes, etc.)
    words = re.findall(r'\b[\w\'-]+\b', content)
    word_count = len(words)
    sentence_count = len(re.findall(r'[.!?]+', content))
    
    results = []
    for keyword in keywords:
        kw = keyword.strip().lower()
        # Count keyword instances (case-insensitive and supports multi-word keywords)
        instances = content.lower().count(kw)
        # Calculate density
        density = (instances / word_count * 100) if word_count > 0 else 0
        results.append({
            "Keyword": keyword,
            "Instances": instances,
            "Density (%)": f"{density:.2f}%"
        })
    
    return word_count, sentence_count, results

# Single URL Analyzer Tab
with tab1:
    st.header("🔍 Single URL Analyzer")
    url = st.text_input("Enter URL to analyze:", placeholder="https://example.com")
    keywords = st.text_input("Enter keywords (comma separated):", placeholder="SEO, content, analysis")
    
    if st.button("Analyze Single URL", type="primary"):
        if url and keywords:
            with st.spinner("Analyzing content..."):
                keywords_list = [k.strip() for k in keywords.split(",")]
                content = get_clean_content(url)
                
                if content:
                    word_count, sentence_count, analysis = analyze_content(content, keywords_list)
                    
                    st.success("Analysis complete! 🎉")
                    st.subheader("📊 Analysis Results")
                    
                    # Metrics
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Words", word_count)
                    with col2:
                        st.metric("Total Sentences", sentence_count)
                    
                    # Keyword Analysis Table
                    st.subheader("🔑 Keyword Analysis")
                    analysis_df = pd.DataFrame(analysis)
                    st.dataframe(analysis_df, use_container_width=True)
                    
                    # Debug: Show extracted content
                    if st.checkbox("Show Extracted Content"):
                        st.text_area("Extracted Content", content, height=300)
                    
                    # CTAs
                    st.download_button(
                        "📥 Download Cleaned Content",
                        content,
                        file_name=f"{url.split('//')[-1].split('/')[0]}_cleaned_content.txt",
                        help="Download the cleaned content for verification."
                    )
                    
                    st.download_button(
                        "📊 Download Keyword Analysis",
                        analysis_df.to_csv(index=False),
                        file_name="keyword_analysis.csv",
                        mime="text/csv",
                        help="Download the keyword analysis report as a CSV file."
                    )
                else:
                    st.warning("No content found on the page. Please check the URL.")
        else:
            st.warning("Please provide both URL and keywords.")

# Bulk Analyzer Tab
with tab2:
    st.header("📚 Bulk URL Analyzer")
    uploaded_file = st.file_uploader("Upload CSV/Excel/TXT file with URLs", type=["csv", "xlsx", "txt"])
    bulk_keywords = st.text_input("Enter keywords for bulk analysis (comma separated):", placeholder="SEO, content, analysis")
    
    if uploaded_file and bulk_keywords and st.button("Analyze Bulk URLs", type="primary"):
        with st.spinner("Analyzing bulk URLs..."):
            try:
                # Read URLs from file
                if uploaded_file.name.endswith(".csv"):
                    urls = pd.read_csv(uploaded_file).iloc[:, 0].dropna().tolist()
                elif uploaded_file.name.endswith(".xlsx"):
                    urls = pd.read_excel(uploaded_file).iloc[:, 0].dropna().tolist()
                elif uploaded_file.name.endswith(".txt"):
                    urls = [line.strip() for line in uploaded_file]
                
                keywords_list = [k.strip() for k in bulk_keywords.split(",")]
                results = []
                
                progress_bar = st.progress(0)
                for i, url in enumerate(urls):
                    content = get_clean_content(url)
                    if content:
                        word_count, sentence_count, analysis = analyze_content(content, keywords_list)
                        # Add results for each URL
                        results.append({
                            "URL": url,
                            "Word Count": word_count,
                            "Sentence Count": sentence_count,
                            **{f"{kw} Density": next((a["Density (%)"] for a in analysis if a["Keyword"] == kw), "0.00%") for kw in keywords_list}
                        })
                    progress_bar.progress((i + 1) / len(urls))
                
                if results:
                    df = pd.DataFrame(results)
                    st.success("Bulk analysis complete! 🎉")
                    st.subheader("📊 Bulk Analysis Results")
                    st.dataframe(df, use_container_width=True)
                    
                    # CTA for Bulk Analysis
                    st.download_button(
                        "📥 Download Bulk Analysis Report",
                        df.to_csv(index=False),
                        file_name="bulk_analysis_report.csv",
                        mime="text/csv",
                        help="Download the bulk analysis report as a CSV file."
                    )
                else:
                    st.warning("No valid content found in provided URLs.")
            except Exception as e:
                st.error(f"Error processing bulk analysis: {str(e)}")

# Keyword Tool Tab
with tab3:
    st.header("🔑 Keyword Analysis Tool")
    text_content = st.text_area("Paste your content here:", height=300, placeholder="Paste your text content here...")
    tool_keywords = st.text_input("Enter keywords to analyze (comma separated):", placeholder="SEO, content, analysis")
    
    if text_content and tool_keywords and st.button("Analyze Keywords", type="primary"):
        with st.spinner("Analyzing keywords..."):
            keywords_list = [k.strip() for k in tool_keywords.split(",")]
            words = re.findall(r'\b[\w\'-]+\b', text_content)
            word_count = len(words)
            
            results = []
            for keyword in keywords_list:
                kw = keyword.lower()
                # Count keyword instances (case-insensitive and supports multi-word keywords)
                instances = text_content.lower().count(kw)
                # Calculate density
                density = (instances / word_count * 100) if word_count > 0 else 0
                results.append({
                    "Keyword": keyword,
                    "Instances": instances,
                    "Density (%)": f"{density:.2f}%"
                })
            
            st.success("Keyword analysis complete! 🎉")
            st.subheader("📊 Analysis Results")
            
            # Metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Words", word_count)
            with col2:
                st.metric("Total Keywords Found", sum(r["Instances"] for r in results))
            
            # Keyword Analysis Table
            st.subheader("🔑 Keyword Analysis")
            analysis_df = pd.DataFrame(results)
            st.dataframe(analysis_df, use_container_width=True)
            
            # CTA for Keyword Tool
            st.download_button(
                "📥 Download Keyword Analysis",
                analysis_df.to_csv(index=False),
                file_name="keyword_analysis.csv",
                mime="text/csv",
                help="Download the keyword analysis report as a CSV file."
            )