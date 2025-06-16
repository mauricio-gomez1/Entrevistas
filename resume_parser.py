from pdfminer.high_level import extract_text
import spacy
import os
from typing import Dict, List, Optional

class ResumeParser:
    def __init__(self):
        """Initialize the resume parser with spaCy model."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spaCy model...")
            os.system("python -m spacy download es_core_news_sm")
            self.nlp = spacy.load("es_core_news_sm")

    def extract_resume_text(self, pdf_path: str) -> Optional[str]:
        """
        Extract text from PDF resume.
        Args:
            pdf_path: Path to the PDF file
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            text = extract_text(pdf_path)
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            return None

    def extract_skills(self, text: str) -> List[str]:
        """
        Extract skills from resume text.
        Args:
            text: Resume text
        Returns:
            List of extracted skills
        """
        # Common technical skills to look for
        technical_skills = [
            "python", "java", "javascript", "c++", "c#", "ruby", "php",
            "html", "css", "react", "angular", "vue", "node.js", "django",
            "flask", "spring", "sql", "nosql", "mongodb", "postgresql",
            "aws", "azure", "gcp", "docker", "kubernetes", "git", "agile",
            "scrum", "machine learning", "ai", "data science", "big data",
            "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn",
            "devops", "ci/cd", "jenkins", "ansible", "terraform",
            "rest api", "graphql", "microservices", "cloud computing",
            "linux", "unix", "bash", "shell scripting", "networking",
            "security", "cybersecurity", "blockchain", "web development",
            "mobile development", "ios", "android", "swift", "kotlin"
        ]
        
        # Extract named entities
        doc = self.nlp(text)
        entities = [ent.text.lower() for ent in doc.ents]
        
        # Find skills from predefined list
        found_skills = []
        for skill in technical_skills:
            if skill in text.lower():
                found_skills.append(skill)
        
        # Add any additional skills found in entities
        for entity in entities:
            if entity not in found_skills and len(entity) > 2:
                found_skills.append(entity)
        
        return list(set(found_skills))

    def analyze_resume(self, pdf_path: str) -> Optional[Dict]:
        """
        Complete resume analysis.
        Args:
            pdf_path: Path to the PDF file
        Returns:
            Dictionary containing analysis results or None if analysis fails
        """
        text = self.extract_resume_text(pdf_path)
        if text:
            skills = self.extract_skills(text)
            return {
                "text": text,
                "skills": skills
            }
        return None