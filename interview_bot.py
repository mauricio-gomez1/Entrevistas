from typing import List, Dict
import random

class InterviewBot:
    def __init__(self):
        # Common interview questions by category
        self.question_templates = {
            'behavioral': [
                "Tell me about a time when you {scenario}.",
                "Describe a situation where you had to {scenario}.",
                "Give me an example of when you {scenario}.",
                "Share a specific instance where you {scenario}."
            ],
            'technical': [
                "How would you approach {scenario}?",
                "Explain your experience with {scenario}.",
                "What's your understanding of {scenario}?",
                "How do you handle {scenario}?"
            ],
            'situational': [
                "What would you do if {scenario}?",
                "How would you handle a situation where {scenario}?",
                "If you were faced with {scenario}, what would be your approach?",
                "Imagine you're in a situation where {scenario}. How would you respond?"
            ]
        }
        
        # Common scenarios based on skills
        self.skill_scenarios = {
            'leadership': [
                "led a team through a challenging project",
                "had to make a difficult decision that affected your team",
                "had to motivate team members during a difficult time",
                "had to resolve a conflict between team members"
            ],
            'problem_solving': [
                "faced a complex technical problem",
                "had to debug a critical issue under pressure",
                "had to optimize a slow-performing system",
                "had to find a creative solution to a challenging problem"
            ],
            'communication': [
                "had to explain a complex technical concept to non-technical stakeholders",
                "had to present your work to senior management",
                "had to write technical documentation",
                "had to collaborate with different teams"
            ],
            'technical': [
                "worked with a new technology or framework",
                "had to learn a new programming language quickly",
                "had to design a scalable system",
                "had to implement a complex feature"
            ]
        }

    def generate_questions(self, skills: List[str], num_questions: int = 5) -> List[Dict]:
        """
        Generate interview questions based on skills.
        Args:
            skills: List of skills from resume
            num_questions: Number of questions to generate
        Returns:
            List of questions with their categories and context
        """
        questions = []
        used_scenarios = set()
        
        # Map skills to question categories
        skill_categories = self._categorize_skills(skills)
        
        while len(questions) < num_questions:
            # Select a random category
            category = random.choice(list(self.question_templates.keys()))
            
            # Get relevant scenarios for the skills
            relevant_scenarios = []
            for skill_category in skill_categories:
                if skill_category in self.skill_scenarios:
                    relevant_scenarios.extend(self.skill_scenarios[skill_category])
            
            if not relevant_scenarios:
                continue
                
            # Select a random scenario
            scenario = random.choice(relevant_scenarios)
            if scenario in used_scenarios:
                continue
                
            used_scenarios.add(scenario)
            
            # Generate question
            template = random.choice(self.question_templates[category])
            question = template.format(scenario=scenario)
            
            questions.append({
                'question': question,
                'category': category,
                'context': scenario
            })
        
        return questions

    def _categorize_skills(self, skills: List[str]) -> List[str]:
        """Categorize skills into general categories."""
        categories = set()
        
        # Simple categorization based on keywords
        for skill in skills:
            skill = skill.lower()
            if any(word in skill for word in ['lead', 'manage', 'team']):
                categories.add('leadership')
            if any(word in skill for word in ['solve', 'debug', 'optimize']):
                categories.add('problem_solving')
            if any(word in skill for word in ['communicate', 'present', 'write']):
                categories.add('communication')
            if any(word in skill for word in ['program', 'code', 'develop', 'design']):
                categories.add('technical')
        
        return list(categories)

    def evaluate_answer(self, question: Dict, answer: str, skills: List[str]) -> Dict:
        """
        Evaluate an answer based on the question and expected skills.
        Args:
            question: Question dictionary
            answer: Candidate's answer
            skills: List of relevant skills
        Returns:
            Dictionary with evaluation results
        """
        # Simple evaluation based on keyword matching
        answer = answer.lower()
        relevant_skills = [skill.lower() for skill in skills]
        
        # Count how many relevant skills were mentioned
        mentioned_skills = [
            skill for skill in relevant_skills
            if skill in answer
        ]
        
        # Calculate basic metrics
        skill_coverage = len(mentioned_skills) / len(relevant_skills) if relevant_skills else 0
        
        return {
            'mentioned_skills': mentioned_skills,
            'skill_coverage': skill_coverage,
            'answer_length': len(answer.split()),
            'evaluation': {
                'completeness': 'high' if skill_coverage > 0.7 else 'medium' if skill_coverage > 0.3 else 'low',
                'relevance': 'high' if len(mentioned_skills) > 0 else 'low'
            }
        } 