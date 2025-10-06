"""
Web Scraping Module using Tavily API (Enhanced for Quick & Comprehensive Information)
Optimized for fast extraction of detailed user information and social links
"""

import os
import json
import requests
import logging
import asyncio
import time
import re
import httpx
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

logger = logging.getLogger(__name__)

# Enhanced cache for multiple query types
_SEARCH_CACHE: Dict[str, Dict[str, Any]] = {}
_CONTENT_CACHE: Dict[str, str] = {}

@dataclass
class PersonInfo:
    """Enhanced data class for person information"""
    name: str
    company: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    github: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    experience: List[str] = None
    education: List[str] = None
    skills: List[str] = None
    recent_news: List[str] = None
    summary: Optional[str] = None
    social_profiles: Dict[str, str] = None
    projects: List[str] = None
    technologies: List[str] = None
    organizations: List[str] = None

@dataclass
class CompanyInfo:
    """Enhanced data class for company information"""
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    founded: Optional[str] = None
    headquarters: Optional[str] = None
    description: Optional[str] = None
    products: List[str] = None
    leadership: List[str] = None
    recent_news: List[str] = None
    financial_info: Optional[str] = None

class TavilyWebScraper:
    """
    Enhanced web scraper using multi-query strategy for comprehensive information
    """
    
    def __init__(self, api_key: str):
        """Initialize Tavily API client"""
        self.api_key = api_key
        self.base_url = "https://api.tavily.com/search"
        self.headers = {"Content-Type": "application/json"}
        
        # Initialize direct Tavily client for fast operations
        self.tavily_client = TavilyClient(api_key)
        
        # Enhanced extraction patterns
        self.skill_tokens = [
            "python", "javascript", "typescript", "java", "go", "rust", "c++", "c#", 
            "react", "node", "fastapi", "django", "flask", "aws", "azure", "gcp", 
            "kubernetes", "docker", "terraform", "postgres", "mysql", "mongodb", 
            "redis", "graphql", "next.js", "pytorch", "tensorflow", "langchain"
        ]
        
        self.role_tokens = [
            "founder", "co-founder", "ceo", "cto", "engineer", "developer", "designer", 
            "architect", "manager", "lead", "researcher", "scientist", "product manager", 
            "data scientist", "analyst", "director", "senior", "principal"
        ]
        
        self.site_targets = [
            "github.com", "linkedin.com/in", "x.com", "twitter.com", "medium.com",
            "dev.to", "crunchbase.com", "youtube.com", "substack.com", "angel.co"
        ]
    
    def search_tavily_cached(self, query: str, ttl: int = 900, max_results: int = 5) -> Dict[str, Any]:
        """Enhanced cached search with configurable results"""
        now = time.time()
        entry = _SEARCH_CACHE.get(query)
        
        if entry and (now - entry["ts"]) < ttl:
            logger.info(f"Cache hit for: {query}")
            return entry["data"]
        
        result = self.search_tavily_enhanced(query, max_results)
        _SEARCH_CACHE[query] = {"ts": now, "data": result}
        return result
    
    def search_tavily_enhanced(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Enhanced Tavily search with better parameters"""
        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "include_raw_content": True,  # Enable for detailed content
                "include_answer": True,
                "search_depth": "advanced"  # Use advanced for comprehensive results
            }
            
            logger.info(f"Enhanced search: {query}")
            response = requests.post(self.base_url, json=payload, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Tavily request failed: {e}")
            return {"results": [], "answer": None}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"results": [], "answer": None}
    
    def quick_user_summary(self, name: str, company: str = None) -> Dict[str, Any]:
        """
        ULTRA FAST user summary extraction using direct Tavily client
        Gets all user information and social links in one quick search
        """
        try:
            logger.info(f"Quick extraction for {name}{f' at {company}' if company else ''}")
            
            # Single comprehensive query like in your example
            query = f"{name}"
            if company:
                query += f" {company}"
            
            # Use direct Tavily client with advanced answer
            response = self.tavily_client.search(
                query=query,
                include_answer="advanced",
                max_results=8,
                include_domains=["linkedin.com", "twitter.com", "x.com", "github.com", "crunchbase.com"],
                include_raw_content=True
            )
            
            # Extract comprehensive information quickly
            user_info = self._extract_quick_summary(response, name, company)
            
            logger.info(f"Quick extraction completed in minimal time")
            return user_info
            
        except Exception as e:
            logger.error(f"Error in quick user summary: {e}")
            return {
                "name": name,
                "company": company,
                "summary": f"Quick profile for {name}",
                "social_links": {},
                "professional_info": {},
                "error": str(e)
            }
    
    def _extract_quick_summary(self, response: Dict[str, Any], name: str, company: str = None) -> Dict[str, Any]:
        """Extract comprehensive information from Tavily response quickly"""
        try:
            # Initialize result structure
            result = {
                "name": name,
                "company": company,
                "summary": "",
                "social_links": {},
                "professional_info": {
                    "title": None,
                    "location": None,
                    "industry": None,
                    "skills": [],
                    "experience": []
                },
                "contact_info": {},
                "recent_activity": [],
                "timestamp": datetime.now().isoformat()
            }
            
            # Extract from Tavily's advanced answer
            if response.get("answer"):
                result["summary"] = response["answer"][:500]  # First 500 chars
            
            # Process search results for detailed info
            results = response.get("results", [])
            
            for item in results:
                url = item.get("url", "")
                title = item.get("title", "")
                content = item.get("content", "")
                
                # Extract social links
                if "linkedin.com/in/" in url:
                    result["social_links"]["linkedin"] = url
                elif any(domain in url for domain in ["twitter.com", "x.com"]):
                    result["social_links"]["twitter"] = url
                elif "github.com" in url:
                    result["social_links"]["github"] = url
                elif "crunchbase.com" in url:
                    result["social_links"]["crunchbase"] = url
                elif "medium.com" in url:
                    result["social_links"]["medium"] = url
                elif "youtube.com" in url:
                    result["social_links"]["youtube"] = url
                
                # Extract professional information
                content_lower = content.lower()
                title_lower = title.lower()
                
                # Extract job title
                if not result["professional_info"]["title"]:
                    for role in self.role_tokens:
                        if role in content_lower or role in title_lower:
                            # Try to extract full title context
                            sentences = content.split('.')
                            for sentence in sentences[:3]:  # Check first 3 sentences
                                if role in sentence.lower():
                                    result["professional_info"]["title"] = sentence.strip()[:100]
                                    break
                            if not result["professional_info"]["title"]:
                                result["professional_info"]["title"] = role.title()
                            break
                
                # Extract skills
                for skill in self.skill_tokens:
                    if skill in content_lower and skill not in result["professional_info"]["skills"]:
                        result["professional_info"]["skills"].append(skill)
                        if len(result["professional_info"]["skills"]) >= 10:  # Limit to 10 skills
                            break
                
                # Extract location (simple patterns)
                import re
                location_patterns = [
                    r'(?:based in|located in|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                    r'([A-Z][a-z]+,\s*[A-Z]{2})',
                    r'([A-Z][a-z]+,\s*[A-Z][a-z]+)'
                ]
                
                if not result["professional_info"]["location"]:
                    for pattern in location_patterns:
                        match = re.search(pattern, content)
                        if match:
                            result["professional_info"]["location"] = match.group(1)
                            break
                
                # Add to recent activity
                if len(result["recent_activity"]) < 5:
                    result["recent_activity"].append({
                        "title": title[:100],
                        "url": url,
                        "snippet": content[:150] + "..." if len(content) > 150 else content
                    })
            
            # Generate comprehensive summary if not from advanced answer
            if not result["summary"] and results:
                summary_parts = [f"{name} is"]
                
                if result["professional_info"]["title"]:
                    summary_parts.append(f"a {result['professional_info']['title']}")
                
                if company:
                    summary_parts.append(f"at {company}")
                
                if result["professional_info"]["location"]:
                    summary_parts.append(f"based in {result['professional_info']['location']}")
                
                if result["professional_info"]["skills"]:
                    top_skills = result["professional_info"]["skills"][:3]
                    summary_parts.append(f"with expertise in {', '.join(top_skills)}")
                
                social_platforms = list(result["social_links"].keys())
                if social_platforms:
                    summary_parts.append(f"Active on {', '.join(social_platforms)}")
                
                result["summary"] = ". ".join(summary_parts) + "."
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting quick summary: {e}")
            return {
                "name": name,
                "company": company,
                "summary": f"Professional profile for {name}" + (f" at {company}" if company else ""),
                "social_links": {},
                "professional_info": {},
                "recent_activity": [],
                "error": str(e)
            }
    
    def scrape_public_profile(self, name: str, company: str = None, username: str = None) -> Dict[str, Any]:
        """
        Enhanced profile scraping using multi-query strategy (based on your working app)
        """
        try:
            start_time = time.time()
            
            # Clean inputs
            name_c = (name or "").strip()
            comp_c = (company or "").strip()
            user_c = (username or "").strip()
            
            # Build comprehensive query variants (precision → recall)
            variants = []
            
            # Core queries
            if name_c and comp_c:
                variants.extend([
                    f"{name_c} {comp_c}",
                    f'"{name_c}" "{comp_c}"',
                    f"{name_c} {comp_c} profile",
                    f"{name_c} {comp_c} biography",
                ])
            
            if name_c and user_c:
                variants.append(f"{name_c} {user_c}")
            
            if user_c:
                variants.append(user_c)
            
            if name_c:
                variants.append(f"{name_c} profile")
            
            # Site-specific queries for comprehensive social media coverage
            site_variants = []
            for site in self.site_targets:
                if name_c and comp_c:
                    site_variants.append(f'"{name_c}" "{comp_c}" site:{site}')
                if name_c:
                    site_variants.append(f'"{name_c}" site:{site}')
                if user_c:
                    site_variants.append(f'"{user_c}" site:{site}')
            
            # Collect results from multiple queries
            aggregated = []
            seen_urls = set()
            executed_queries = []
            
            # Phase 1: Core variants
            for query in variants[:4]:  # Limit core queries for speed
                results = self.search_tavily_cached(query, ttl=300, max_results=5)
                executed_queries.append(query)
                
                for result in results.get("results", []):
                    url = result.get("url")
                    if url and url not in seen_urls:
                        aggregated.append(result)
                        seen_urls.add(url)
                
                if len(aggregated) >= 12:  # Good coverage
                    break
            
            # Phase 2: Site-specific if we need more coverage
            if len(aggregated) < 8:
                for query in site_variants[:6]:  # Limited site queries
                    results = self.search_tavily_cached(query, ttl=600, max_results=3)
                    executed_queries.append(query)
                    
                    for result in results.get("results", []):
                        url = result.get("url")
                        if url and url not in seen_urls:
                            aggregated.append(result)
                            seen_urls.add(url)
                    
                    if len(aggregated) >= 15:
                        break
            
            # Extract structured information
            extracted_data = self._extract_structured_info(aggregated, name_c, comp_c)
            
            # Generate comprehensive profile
            profile = {
                "query": variants[0] if variants else f"{name_c} {comp_c}",
                "queries": executed_queries,
                "results": aggregated[:12],  # Limit for response size
                "source": "tavily",
                "result_count": len(aggregated),
                "scraped_at": datetime.utcnow().isoformat() + "Z",
                "name": name_c or None,
                "company": comp_c or None,
                "username": user_c or None,
                "extraction_time": round(time.time() - start_time, 2),
                **extracted_data
            }
            
            logger.info(f"Enhanced profile extraction completed in {profile['extraction_time']}s")
            return profile
            
        except Exception as e:
            logger.error(f"Error in enhanced profile scraping: {e}")
            return {
                "name": name,
                "company": company,
                "error": str(e),
                "extraction_time": 0
            }
    def _extract_structured_info(self, results: List[Dict[str, Any]], name: str, company: str) -> Dict[str, Any]:
        """
        Extract comprehensive structured information from search results
        """
        try:
            # Initialize collections
            technologies: Set[str] = set()
            roles: Set[str] = set()
            organizations: Set[str] = set()
            projects: Set[str] = set()
            locations: Set[str] = set()
            social_profiles: Dict[str, str] = {}
            
            # Location pattern
            loc_pattern = re.compile(
                r"\b(San Francisco|New York|London|Berlin|Paris|Toronto|Sydney|Singapore|"
                r"Bangalore|Mumbai|Dubai|Austin|Seattle|Los Angeles|Chicago|Boston|"
                r"Amsterdam|Barcelona|Madrid|Rome|Tokyo|Hong Kong)\b", re.I
            )
            
            # Process each result
            for result in results:
                content = result.get("content", "") or result.get("raw_content", "") or ""
                title = result.get("title", "") or ""
                url = result.get("url", "") or ""
                
                # Combine text for analysis
                full_text = f"{title} {content}".lower()
                
                # Extract technologies/skills
                for skill in self.skill_tokens:
                    if skill in full_text:
                        technologies.add(skill)
                
                # Extract roles/positions
                for role in self.role_tokens:
                    if role in full_text:
                        roles.add(role)
                
                # Extract organizations (pattern: "at Company Name")
                org_matches = re.findall(
                    r" at ([A-Z][A-Za-z0-9&._-]{2,}(?: [A-Z][A-Za-z0-9&._-]{1,}){0,3})", 
                    content
                )
                for match in org_matches:
                    org_name = match[0] if isinstance(match, tuple) else match
                    organizations.add(org_name.strip())
                
                # Extract GitHub projects
                if "github.com" in url:
                    gh_match = re.match(r"https?://github\.com/([^/]+/[^/#?]+)", url)
                    if gh_match:
                        projects.add(gh_match.group(1))
                
                # Extract locations
                for loc_match in loc_pattern.findall(content):
                    locations.add(loc_match)
                
                # Extract social profiles
                self._extract_social_profiles(url, social_profiles)
            
            # Get LinkedIn profile specifically
            linkedin_url = self._find_linkedin_profile(results, name, company)
            if linkedin_url:
                social_profiles["linkedin"] = linkedin_url
            
            # Generate summary from top results
            summary = self._generate_profile_summary(results[:8], name, company, technologies, roles, organizations)
            
            return {
                "summary": summary,
                "technologies": sorted(list(technologies))[:20],
                "roles": sorted(list(roles))[:10],
                "organizations": sorted(list(organizations))[:10],
                "projects": sorted(list(projects))[:10],
                "locations": sorted(list(locations))[:5],
                "social_profiles": social_profiles,
                "top_titles": [r.get("title", "") for r in results[:5] if r.get("title")]
            }
            
        except Exception as e:
            logger.error(f"Error in structured extraction: {e}")
            return {
                "summary": f"Professional profile for {name}" + (f" at {company}" if company else ""),
                "technologies": [],
                "roles": [],
                "organizations": [],
                "projects": [],
                "locations": [],
                "social_profiles": {},
                "top_titles": []
            }
    
    def _extract_social_profiles(self, url: str, social_profiles: Dict[str, str]) -> None:
        """Extract social media profiles from URLs"""
        if not url:
            return
            
        url_lower = url.lower()
        domain = url.split('/')[2] if len(url.split('/')) > 2 else ""
        
        if "github.com" in url_lower and "github" not in social_profiles:
            social_profiles["github"] = url
        elif "linkedin.com/in/" in url_lower and "linkedin" not in social_profiles:
            social_profiles["linkedin"] = url
        elif any(x in url_lower for x in ["twitter.com", "x.com"]) and "twitter" not in social_profiles:
            social_profiles["twitter"] = url
        elif "medium.com" in url_lower and "medium" not in social_profiles:
            social_profiles["medium"] = url
        elif "dev.to" in url_lower and "dev.to" not in social_profiles:
            social_profiles["dev.to"] = url
        elif "youtube.com" in url_lower and "youtube" not in social_profiles:
            social_profiles["youtube"] = url
    
    def _find_linkedin_profile(self, results: List[Dict[str, Any]], name: str, company: str) -> Optional[str]:
        """Find the most relevant LinkedIn profile"""
        linkedin_urls = []
        
        for result in results:
            url = result.get("url", "")
            if "linkedin.com/in/" in url:
                title = result.get("title", "").lower()
                content = result.get("content", "").lower()
                
                # Score relevance
                score = 0
                if name.lower() in title or name.lower() in content:
                    score += 3
                if company and company.lower() in title or company and company.lower() in content:
                    score += 2
                
                linkedin_urls.append((url, score))
        
        if linkedin_urls:
            # Return highest scoring LinkedIn profile
            linkedin_urls.sort(key=lambda x: x[1], reverse=True)
            return linkedin_urls[0][0]
        
        return None
    
    def _generate_profile_summary(self, results: List[Dict[str, Any]], name: str, company: str, 
                                technologies: Set[str], roles: Set[str], organizations: Set[str]) -> str:
        """Generate a comprehensive profile summary"""
        try:
            # Extract key information
            role_list = list(roles)[:3]
            tech_list = list(technologies)[:5]
            org_list = list(organizations)[:3]
            
            # Build summary components
            summary_parts = []
            
            # Basic introduction
            intro = f"{name}"
            if role_list:
                intro += f" is a {', '.join(role_list)}"
            if company:
                intro += f" at {company}"
            summary_parts.append(intro + ".")
            
            # Technical skills
            if tech_list:
                summary_parts.append(f"Skilled in {', '.join(tech_list)}.")
            
            # Organizations/experience
            if org_list and org_list != [company]:
                summary_parts.append(f"Previously associated with {', '.join(org_list)}.")
            
            # Extract notable achievements from content
            achievements = []
            for result in results[:3]:
                content = result.get("content", "")
                title = result.get("title", "")
                
                # Look for achievement indicators
                if any(keyword in content.lower() for keyword in ["founded", "created", "built", "developed", "launched"]):
                    if len(content) > 50:
                        achievements.append(content[:100] + "...")
                        break
            
            if achievements:
                summary_parts.append(achievements[0])
            
            return " ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Professional profile for {name}" + (f" at {company}" if company else "")
    
    def extract_person_info(self, name: str, company: str = None) -> PersonInfo:
        """
        Extract detailed person information using enhanced multi-query strategy
        
        Args:
            name: Person's name
            company: Optional company name
            
        Returns:
            PersonInfo object with extracted data
        """
        try:
            logger.info(f"Extracting person info for {name}{f' at {company}' if company else ''}")
            
            # Initialize person info
            person_info = PersonInfo(name=name, company=company)
            
            # Multi-query strategy for comprehensive data
            queries = [
                f"{name} LinkedIn profile {company or ''}",
                f"{name} {company or ''} executive biography",
                f"{name} professional background experience",
                f"{name} social media profiles contact"
            ]
            
            all_results = []
            for query in queries:
                try:
                    results = self.search_tavily_cached(query, ttl=600, max_results=3)
                    if results and "results" in results:
                        all_results.extend(results["results"])
                except Exception as e:
                    logger.warning(f"Query failed: {query} - {e}")
                    continue
            
            # Process all results
            person_info = self._process_person_results(person_info, all_results)
            
            # Extract structured information
            structured_info = self._extract_structured_info(all_results, name, company or "")
            
            # Merge structured info into person_info
            if structured_info:
                person_info.title = person_info.title or structured_info.get("title")
                person_info.location = person_info.location or structured_info.get("location")
                person_info.linkedin = person_info.linkedin or structured_info.get("social_profiles", {}).get("linkedin")
                person_info.twitter = person_info.twitter or structured_info.get("social_profiles", {}).get("twitter")
                
                # Add additional structured data
                if structured_info.get("skills"):
                    person_info.skills = person_info.skills or []
                    person_info.skills.extend(structured_info["skills"][:5])  # Top 5 skills
                
                if structured_info.get("projects"):
                    person_info.recent_news = person_info.recent_news or []
                    for project in structured_info["projects"][:3]:  # Top 3 projects
                        person_info.recent_news.append(f"Project: {project}")
            
            return person_info
            
        except Exception as e:
            logger.error(f"Error extracting person info: {e}")
            return PersonInfo(name=name, company=company)
    
    def extract_company_info(self, company_name: str) -> CompanyInfo:
        """
        Ultra-fast company information extraction
        
        Args:
            company_name: Company name
            
        Returns:
            CompanyInfo object with extracted data
        """
        try:
            # Single focused query
            query = f"{company_name} company website industry"
            
            # Use cached search for speed
            results = self.search_tavily_cached(query, ttl=600)  # 10-minute cache for companies
            
            company_info = CompanyInfo(name=company_name)
            
            # Quick extraction from answer
            if results.get("answer"):
                answer = results["answer"]
                company_info.description = answer[:200]
                company_info.website = self._extract_website_url(answer)
                company_info.industry = self._quick_extract_industry(answer)
            
            # Quick processing of top result only
            if results.get("results") and len(results["results"]) > 0:
                top_result = results["results"][0]
                url = top_result.get("url", "")
                
                if not company_info.website and self._is_company_website(url, company_name):
                    company_info.website = url
            
            logger.info(f"Fast company extraction completed for {company_name}")
            return company_info
            
        except Exception as e:
            logger.error(f"Error in fast company extraction: {e}")
            return CompanyInfo(name=company_name)
    
    def get_comprehensive_info(self, name: str, company: str = None) -> Dict[str, Any]:
        """
        Get comprehensive information about a person and their company
        Optimized for speed and comprehensive data extraction
        
        Args:
            name: Person's name
            company: Optional company name
            
        Returns:
            Dictionary with comprehensive information
        """
        try:
            logger.info(f"Gathering comprehensive info for {name}{f' at {company}' if company else ''}")
            
            # Extract person information
            person_info = self.extract_person_info(name, company)
            
            # Extract company information if provided
            company_info = None
            if company:
                company_info = self.extract_company_info(company)
            
            # Get social media presence
            social_info = self._extract_social_media_info(name, company)
            
            # Get recent news and mentions
            news_info = self._extract_news_mentions(name, company)
            
            # Get industry insights
            industry_info = None
            if company:
                industry_info = self._extract_industry_insights(company)
            
            return {
                "person": person_info.__dict__,
                "company": company_info.__dict__ if company_info else None,
                "social_media": social_info,
                "news_mentions": news_info,
                "industry_insights": industry_info,
                "timestamp": datetime.now().isoformat(),
                "search_successful": True
            }
            
        except Exception as e:
            logger.error(f"Error gathering comprehensive info: {e}")
            return {
                "person": None,
                "company": None,
                "social_media": {},
                "news_mentions": [],
                "industry_insights": None,
                "timestamp": datetime.now().isoformat(),
                "search_successful": False,
                "error": str(e)
            }
    
    def _extract_social_media_info(self, name: str, company: str = None) -> Dict[str, str]:
        """Extract social media information (optimized for speed)"""
        try:
            social_info = {"linkedin": None, "twitter": None, "github": None}
            
            # Single comprehensive search for social media
            social_query = f"{name} LinkedIn Twitter GitHub social media {company or ''}"
            results = self.search_tavily_cached(social_query, ttl=600, max_results=5)
            
            for result in results.get("results", []):
                url = result.get("url", "")
                if "linkedin.com/in/" in url and not social_info["linkedin"]:
                    social_info["linkedin"] = url
                elif any(domain in url for domain in ["twitter.com", "x.com"]) and not social_info["twitter"]:
                    social_info["twitter"] = url
                elif "github.com" in url and not social_info["github"]:
                    social_info["github"] = url
            
            return social_info
            
        except Exception as e:
            logger.error(f"Error extracting social media info: {e}")
            return {}
    
    def _extract_news_mentions(self, name: str, company: str = None) -> List[Dict[str, Any]]:
        """Extract recent news mentions (optimized for speed)"""
        try:
            news_mentions = []
            
            # Single quick search for recent news
            news_query = f"{name} {company or ''} news recent"
            news_results = self.search_tavily_cached(news_query, ttl=300, max_results=3)
            
            for result in news_results.get("results", []):
                mention = {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("content", "")[:150] + "..." if result.get("content") else "",
                    "source": result.get("url", "").split("/")[2] if result.get("url") else ""
                }
                if mention["title"]:
                    news_mentions.append(mention)
            
            return news_mentions[:2]  # Return top 2 mentions for speed
            
        except Exception as e:
            logger.error(f"Error extracting news mentions: {e}")
            return []
    
    def _extract_industry_insights(self, company: str) -> Dict[str, Any]:
        """Extract industry insights for the company (optimized for speed)"""
        try:
            insights = {
                "industry_trends": [],
                "competitors": [],
                "market_position": None
            }
            
            # Single quick search instead of multiple
            insights_query = f"{company} industry competitors market"
            results = self.search_tavily_cached(insights_query, ttl=600, max_results=2)
            
            for result in results.get("results", []):
                content = result.get("content", "").lower()
                title = result.get("title", "")
                
                # Quick trend extraction
                if any(keyword in content for keyword in ["trend", "market", "growth"]):
                    trend = {
                        "title": title,
                        "insight": result.get("content", "")[:100] + "..." if result.get("content") else ""
                    }
                    insights["industry_trends"].append(trend)
                
                # Quick competitor extraction
                if any(keyword in content for keyword in ["competitor", "rival", "versus"]):
                    competitor = {
                        "source": title,
                        "info": result.get("content", "")[:80] + "..." if result.get("content") else ""
                    }
                    insights["competitors"].append(competitor)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting industry insights: {e}")
            return {}
        """
        Enhanced comprehensive information gathering with detailed extraction
        """
        try:
            start_time = time.time()
            
            # Use the enhanced profile scraping method
            profile_data = self.scrape_public_profile(name, company)
            
            # Structure the response for compatibility with existing code
            result = {
                "person": {
                    "name": name,
                    "company": company or "",
                    "title": self._extract_title_from_profile(profile_data),
                    "linkedin": profile_data.get("social_profiles", {}).get("linkedin"),
                    "bio": profile_data.get("summary", ""),
                    "location": profile_data.get("locations", [None])[0] if profile_data.get("locations") else None,
                    "technologies": profile_data.get("technologies", []),
                    "roles": profile_data.get("roles", []),
                    "projects": profile_data.get("projects", [])
                },
                "company": {
                    "name": company or "",
                    "website": None,
                    "industry": self._extract_industry_from_profile(profile_data),
                    "description": None
                } if company else None,
                "social_media": profile_data.get("social_profiles", {}),
                "news_mentions": self._extract_news_from_profile(profile_data),
                "industry_insights": [],
                "extraction_time": round(time.time() - start_time, 2),
                "detailed_profile": profile_data  # Include full profile data
            }
            
            logger.info(f"Enhanced comprehensive extraction completed in {result['extraction_time']}s")
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive info extraction: {e}")
            return {
                "person": {"name": name, "company": company or ""},
                "company": {"name": company} if company else None,
                "social_media": {},
                "news_mentions": [],
                "industry_insights": [],
                "extraction_time": 0,
                "error": str(e)
            }
    
    def _extract_title_from_profile(self, profile_data: Dict[str, Any]) -> Optional[str]:
        """Extract job title from profile data"""
        roles = profile_data.get("roles", [])
        if roles:
            # Return the most senior-sounding role
            senior_roles = ["ceo", "cto", "founder", "director", "senior", "principal", "lead"]
            for role in roles:
                if any(sr in role.lower() for sr in senior_roles):
                    return role.title()
            return roles[0].title()
        return None
    
    def _extract_industry_from_profile(self, profile_data: Dict[str, Any]) -> Optional[str]:
        """Extract industry from profile data"""
        technologies = profile_data.get("technologies", [])
        if technologies:
            # Map technologies to industries
            if any(tech in ["python", "javascript", "react", "node"] for tech in technologies):
                return "Technology"
            elif any(tech in ["aws", "azure", "kubernetes"] for tech in technologies):
                return "Cloud Computing"
            elif any(tech in ["pytorch", "tensorflow"] for tech in technologies):
                return "Artificial Intelligence"
        return None
    
    def _extract_news_from_profile(self, profile_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract news mentions from profile data"""
        news_mentions = []
        results = profile_data.get("results", [])
        
        for result in results[:3]:
            title = result.get("title", "")
            url = result.get("url", "")
            content = result.get("content", "")
            
            # Check if it looks like news
            if any(keyword in title.lower() for keyword in ["news", "press", "announcement", "interview"]):
                news_mentions.append({
                    "title": title,
                    "url": url,
                    "snippet": content[:150] + "..." if content else ""
                })
        
        return news_mentions
    
    def _process_person_results(self, person_info: PersonInfo, results: List[Dict]) -> PersonInfo:
        """Process search results to extract person information"""
        try:
            for result in results:
                content = result.get("content", "").lower()
                url = result.get("url", "")
                
                # Extract LinkedIn
                if "linkedin.com" in url and not person_info.linkedin:
                    person_info.linkedin = url
                
                # Extract Twitter
                if "twitter.com" in url and not person_info.twitter:
                    person_info.twitter = url
                
                # Extract title/position
                if not person_info.title:
                    person_info.title = self._extract_title(content)
                
                # Extract location
                if not person_info.location:
                    person_info.location = self._extract_location(content)
                
                # Collect experience and education
                if person_info.experience is None:
                    person_info.experience = []
                if person_info.education is None:
                    person_info.education = []
                if person_info.skills is None:
                    person_info.skills = []
                if person_info.recent_news is None:
                    person_info.recent_news = []
                
                # Add to recent news if it's a news article
                if any(news_indicator in url for news_indicator in ["news", "press", "article", "blog"]):
                    person_info.recent_news.append(result.get("title", ""))
            
            return person_info
            
        except Exception as e:
            logger.error(f"Error processing person results: {e}")
            return person_info
    
    def _extract_title(self, content: str) -> Optional[str]:
        """Extract job title from content"""
        if not content:
            return None
        content_lower = content.lower()
        common_titles = [
            "ceo", "cto", "cfo", "president", "vice president", "vp", 
            "director", "manager", "engineer", "developer", "founder", 
            "co-founder", "senior", "lead", "principal", "architect"
        ]
        
        for title in common_titles:
            if title in content_lower:
                # Try to extract full title context
                sentences = content.split('.')
                for sentence in sentences:
                    if title in sentence.lower():
                        return sentence.strip()[:50]
                return title.title()
        return None
    
    def _extract_location(self, content: str) -> Optional[str]:
        """Extract location from content"""
        if not content:
            return None
        import re
        # Look for location patterns
        location_patterns = [
            r'(?:located|based|from)\s+(?:in\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z]{2})?)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})',
            r'([A-Z][a-z]+,\s*[A-Z][a-z]+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        return None
    
    def _process_company_results(self, company_info: CompanyInfo, results: List[Dict]) -> CompanyInfo:
        """Process search results to extract company information"""
        try:
            for result in results:
                content = result.get("content", "").lower()
                url = result.get("url", "")
                
                # Extract website
                if not company_info.website and self._is_company_website(url, company_info.name):
                    company_info.website = url
                
                # Extract industry
                if not company_info.industry:
                    company_info.industry = self._extract_industry(content)
                
                # Extract description
                if not company_info.description:
                    company_info.description = result.get("content", "")[:300]
                
                # Initialize lists if None
                if company_info.products is None:
                    company_info.products = []
                if company_info.leadership is None:
                    company_info.leadership = []
                if company_info.recent_news is None:
                    company_info.recent_news = []
                
                # Add to recent news if it's a news article
                if any(news_indicator in url for news_indicator in ["news", "press", "article", "blog"]):
                    company_info.recent_news.append(result.get("title", ""))
            
            return company_info
            
        except Exception as e:
            logger.error(f"Error processing company results: {e}")
            return company_info
    
    def _extract_linkedin_url(self, text: str) -> Optional[str]:
        """Extract LinkedIn URL from text"""
        import re
        linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+'
        match = re.search(linkedin_pattern, text)
        return match.group(0) if match else None
    
    def _extract_website_url(self, text: str) -> Optional[str]:
        """Extract website URL from text"""
        import re
        url_pattern = r'https?://[^\s<>"\'{}|\\^`\[\]]+'
        matches = re.findall(url_pattern, text)
        return matches[0] if matches else None
    
    def _extract_founded_year(self, text: str) -> Optional[str]:
        """Extract founding year from text"""
        import re
        year_pattern = r'\b(19|20)\d{2}\b'
        matches = re.findall(year_pattern, text)
        return matches[0] if matches else None
    
    def _extract_title(self, content: str) -> Optional[str]:
        """Extract job title from content"""
        title_keywords = ["ceo", "cto", "cfo", "president", "director", "manager", "engineer", "developer", "analyst"]
        for keyword in title_keywords:
            if keyword in content:
                # Extract surrounding context
                words = content.split()
                for i, word in enumerate(words):
                    if keyword in word:
                        # Get context around the keyword
                        start = max(0, i-2)
                        end = min(len(words), i+3)
                        return " ".join(words[start:end]).title()
        return None
    
    def _quick_extract_title(self, text: str) -> Optional[str]:
        """Ultra-fast title extraction"""
        if not text:
            return None
        text_lower = text.lower()
        titles = ["ceo", "cto", "cfo", "president", "director", "manager", "engineer", "developer", "founder"]
        for title in titles:
            if title in text_lower:
                return title.upper() if len(title) <= 3 else title.title()
        return None
    
    def _quick_extract_industry(self, text: str) -> Optional[str]:
        """Ultra-fast industry extraction"""
        if not text:
            return None
        text_lower = text.lower()
        industries = ["technology", "tech", "software", "finance", "healthcare", "education", "retail", "consulting"]
        for industry in industries:
            if industry in text_lower:
                return industry.title()
        return None
    
    def _extract_social_media_fast(self, name: str, company: str = None) -> Dict[str, str]:
        """Ultra-fast social media extraction (single query)"""
        try:
            query = f"{name} LinkedIn Twitter social media {company or ''}"
            results = self.search_tavily_cached(query, ttl=600)
            
            social_info = {}
            
            # Quick extraction from results
            for result in results.get("results", [])[:2]:  # Only check top 2
                url = result.get("url", "")
                if "linkedin.com/in/" in url and "linkedin" not in social_info:
                    social_info["linkedin"] = url
                elif any(domain in url for domain in ["twitter.com", "x.com"]) and "twitter" not in social_info:
                    social_info["twitter"] = url
                elif "github.com" in url and "github" not in social_info:
                    social_info["github"] = url
            
            return social_info
        except Exception:
            return {}
    
    def _extract_news_fast(self, name: str, company: str = None) -> List[Dict[str, str]]:
        """Ultra-fast news extraction (single query)"""
        try:
            query = f"{name} {company or ''} news recent"
            results = self.search_tavily_cached(query, ttl=300)
            
            news_mentions = []
            
            # Quick extraction from top result only
            if results.get("results") and len(results["results"]) > 0:
                result = results["results"][0]
                if any(keyword in result.get("title", "").lower() for keyword in ["news", "press", "announcement"]):
                    news_mentions.append({
                        "title": result.get("title", "")[:100],
                        "url": result.get("url", ""),
                        "snippet": result.get("content", "")[:100] + "..." if result.get("content") else ""
                    })
            
            return news_mentions
        except Exception:
            return []
        """Process person search results quickly"""
        try:
            for result in results[:3]:  # Only process top 3 results
                content = result.get("content", "").lower()
                url = result.get("url", "")
                
                # Quick LinkedIn extraction
                if "linkedin.com" in url and not person_info.linkedin:
                    person_info.linkedin = url
                
                # Quick title extraction
                if not person_info.title and any(keyword in content for keyword in ["ceo", "director", "manager", "engineer"]):
                    person_info.title = self._extract_title(content)
                
                # Quick location extraction  
                if not person_info.location:
                    person_info.location = self._extract_location(content)
            
            return person_info
        except Exception as e:
            logger.error(f"Error in fast person processing: {e}")
            return person_info

    def _process_company_results_fast(self, company_info: CompanyInfo, results: List[Dict]) -> CompanyInfo:
        """Process company search results quickly"""
        try:
            for result in results[:3]:  # Only process top 3 results
                content = result.get("content", "").lower()
                url = result.get("url", "")
                
                # Quick website extraction
                if not company_info.website and "http" in content:
                    company_info.website = self._extract_website_url(result.get("content", ""))
                
                # Quick industry extraction
                if not company_info.industry:
                    company_info.industry = self._extract_industry(content)
                
                # Quick size extraction
                if not company_info.size and any(keyword in content for keyword in ["employees", "team", "staff"]):
                    company_info.size = self._extract_size(content)
            
            return company_info
        except Exception as e:
            logger.error(f"Error in fast company processing: {e}")
            return company_info

    def _extract_industry(self, text: str) -> Optional[str]:
        """Extract industry from text"""
        industries = ["technology", "finance", "healthcare", "education", "retail", "manufacturing", "consulting", "marketing", "software"]
        for industry in industries:
            if industry in text.lower():
                return industry.title()
        return None

    def _extract_size(self, text: str) -> Optional[str]:
        """Extract company size from text"""
        import re
        size_pattern = r'(\d+[-–]\d+|\d+\+?)\s*(employees?|people|staff)'
        match = re.search(size_pattern, text.lower())
        return match.group(0) if match else None

    def _extract_location(self, content: str) -> Optional[str]:
        """Extract location from content"""
        # Look for common location patterns
        locations = ["new york", "california", "london", "san francisco", "seattle", "boston", "chicago", "austin"]
        content_lower = content.lower()
        for location in locations:
            if location in content_lower:
                return location.title()
        return None
        """Extract location from content"""
        location_keywords = ["based in", "located in", "from", "lives in", "works in"]
        for keyword in location_keywords:
            if keyword in content:
                # Extract location after keyword
                parts = content.split(keyword)
                if len(parts) > 1:
                    location_part = parts[1].split()[0:3]  # Get next few words
                    return " ".join(location_part).title()
        return None
    
    def _extract_industry(self, content: str) -> Optional[str]:
        """Extract industry from content"""
        industry_keywords = ["technology", "software", "finance", "healthcare", "consulting", "manufacturing", "retail", "education"]
        for keyword in industry_keywords:
            if keyword in content:
                return keyword.title()
        return None
    
    def _is_company_website(self, url: str, company_name: str) -> bool:
        """Check if URL is likely the company's official website"""
        company_words = company_name.lower().split()
        url_lower = url.lower()
        return any(word in url_lower for word in company_words if len(word) > 3)
    
    def _extract_social_media_info(self, name: str, company: str = None) -> Dict[str, Any]:
        """Extract social media information (optimized for speed)"""
        try:
            social_info = {
                "linkedin": None,
                "twitter": None,
                "github": None,
                "other_profiles": []
            }
            
            # Single comprehensive query instead of multiple
            social_query = f"{name} LinkedIn Twitter GitHub profile {company or ''}"
            results = self.search_tavily(social_query, search_depth="basic", max_results=3)
            
            # Quick extraction from results
            for result in results.get("results", []):
                url = result.get("url", "")
                if "linkedin.com/in/" in url and not social_info["linkedin"]:
                    social_info["linkedin"] = url
                elif any(domain in url for domain in ["twitter.com", "x.com"]) and not social_info["twitter"]:
                    social_info["twitter"] = url
                elif "github.com" in url and not social_info["github"]:
                    social_info["github"] = url
            
            return social_info
            
        except Exception as e:
            logger.error(f"Error extracting social media info: {e}")
            return {}
    
    def _extract_news_mentions(self, name: str, company: str = None) -> List[Dict[str, Any]]:
        """Extract recent news mentions (optimized for speed)"""
        try:
            news_mentions = []
            
            # Single quick search for recent news
            news_query = f"{name} {company or ''} news recent"
            news_results = self.search_tavily_cached(news_query, ttl=300, max_results=3)
            
            for result in news_results.get("results", []):
                mention = {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("content", "")[:150] + "..." if result.get("content") else "",
                    "source": result.get("url", "").split("/")[2] if result.get("url") else ""
                }
                if mention["title"]:
                    news_mentions.append(mention)
            
            return news_mentions[:2]  # Return top 2 mentions for speed
            
        except Exception as e:
            logger.error(f"Error extracting news mentions: {e}")
            return []
    
    def _extract_industry_insights(self, company: str) -> Dict[str, Any]:
        """Extract industry insights for the company (optimized for speed)"""
        try:
            insights = {
                "industry_trends": [],
                "competitors": [],
                "market_position": None
            }
            
            # Single quick search instead of multiple
            insights_query = f"{company} industry competitors market"
            results = self.search_tavily_cached(insights_query, ttl=600, max_results=2)
            
            for result in results.get("results", []):
                content = result.get("content", "").lower()
                title = result.get("title", "")
                
                # Quick trend extraction
                if any(keyword in content for keyword in ["trend", "market", "growth"]):
                    trend = {
                        "title": title,
                        "insight": result.get("content", "")[:100] + "..." if result.get("content") else ""
                    }
                    insights["industry_trends"].append(trend)
                
                # Quick competitor extraction
                if any(keyword in content for keyword in ["competitor", "rival", "versus"]):
                    competitor = {
                        "source": title,
                        "info": result.get("content", "")[:80] + "..." if result.get("content") else ""
                    }
                    insights["competitors"].append(competitor)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting industry insights: {e}")
            return {}


# Factory function to create scraper instance
def create_scraper(api_key: str = None) -> TavilyWebScraper:
    """
    Create a TavilyWebScraper instance
    
    Args:
        api_key: Tavily API key (if None, will try to get from environment)
        
    Returns:
        TavilyWebScraper instance
    """
    if not api_key:
        api_key = os.getenv("TAVILY_API_KEY")
    
    if not api_key:
        raise ValueError("Tavily API key is required. Set TAVILY_API_KEY environment variable.")
    
    return TavilyWebScraper(api_key)


# Example usage
if __name__ == "__main__":
    # Test the scraper
    scraper = create_scraper()
    
    # Test person search
    person_info = scraper.extract_person_info("John Doe", "Microsoft")
    print("Person Info:", json.dumps(person_info.__dict__, indent=2))
    
    # Test company search
    company_info = scraper.extract_company_info("Microsoft")
    print("Company Info:", json.dumps(company_info.__dict__, indent=2))
    
    # Test comprehensive search
    comprehensive_info = scraper.get_comprehensive_info("John Doe", "Microsoft")
    print("Comprehensive Info:", json.dumps(comprehensive_info, indent=2))