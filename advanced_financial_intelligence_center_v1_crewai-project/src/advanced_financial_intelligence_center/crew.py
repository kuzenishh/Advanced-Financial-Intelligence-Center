import os

from crewai import LLM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
	SerperDevTool
)
from advanced_financial_intelligence_center.tools.financial_news_sentiment_analyzer import FinancialNewsSentimentAnalyzer
from advanced_financial_intelligence_center.tools.simple_technical_analysis_tool import SimpleTechnicalAnalysisTool
from advanced_financial_intelligence_center.tools.enhanced_technical_analysis_tool import EnhancedTechnicalAnalysisTool
from advanced_financial_intelligence_center.tools.enhanced_technical_tool import EnhancedTechnicalAnalysisTool
from advanced_financial_intelligence_center.tools.market_data_aggregator import MarketDataAggregatorTool
from advanced_financial_intelligence_center.tools.additional_data_sources_integrator import AdditionalDataSourcesIntegratorTool
from advanced_financial_intelligence_center.tools.financial_data_validator import FinancialDataValidator
from advanced_financial_intelligence_center.tools.reporting_notification_system import AutomatedReportingNotificationTool
from advanced_financial_intelligence_center.tools.economic_sentiment_analyzer import EconomicSentimentAnalyzerTool
from advanced_financial_intelligence_center.tools.financial_data_quality_inspector import FinancialDataQualityInspectorTool
from advanced_financial_intelligence_center.tools.real_market_data_fetcher import RealMarketDataFetcher
from advanced_financial_intelligence_center.tools.technical_indicators_calculator import TechnicalIndicatorsCalculator




@CrewBase
class AdvancedFinancialIntelligenceCenterCrew:
    """AdvancedFinancialIntelligenceCenter crew"""

    
    @agent
    def financial_market_analysis_supervisor(self) -> Agent:
        
        return Agent(
            config=self.agents_config["financial_market_analysis_supervisor"],
            
            
            tools=[				AutomatedReportingNotificationTool()],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            
            
            max_execution_time=None,
            llm=LLM(
                model="openai/gpt-4o-mini",
                temperature=0.7,
                
            ),
            
        )
    
    @agent
    def comprehensive_news_and_economic_events_analyst(self) -> Agent:
        
        return Agent(
            config=self.agents_config["comprehensive_news_and_economic_events_analyst"],
            
            
            tools=[				FinancialNewsSentimentAnalyzer(),
				SerperDevTool(),
				EconomicSentimentAnalyzerTool()],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            
            
            max_execution_time=None,
            llm=LLM(
                model="openai/gpt-4o-mini",
                temperature=0.7,
                
            ),
            
        )
    
    @agent
    def risk_assessment_and_investment_advisor(self) -> Agent:
        
        return Agent(
            config=self.agents_config["risk_assessment_and_investment_advisor"],
            
            
            tools=[],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            
            
            max_execution_time=None,
            llm=LLM(
                model="openai/gpt-4o-mini",
                temperature=0.7,
                
            ),
            
        )
    
    @agent
    def enhanced_technical_analyst(self) -> Agent:
        
        return Agent(
            config=self.agents_config["enhanced_technical_analyst"],
            
            
            tools=[				SimpleTechnicalAnalysisTool(),
				EnhancedTechnicalAnalysisTool(),
				EnhancedTechnicalAnalysisTool(),
				EnhancedTechnicalAnalysisTool(),
				TechnicalIndicatorsCalculator()],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            
            
            max_execution_time=None,
            llm=LLM(
                model="openai/gpt-4o-mini",
                temperature=0.7,
                
            ),
            
        )
    
    @agent
    def enhanced_real_time_market_data_specialist(self) -> Agent:
        
        return Agent(
            config=self.agents_config["enhanced_real_time_market_data_specialist"],
            
            
            tools=[				MarketDataAggregatorTool(),
				FinancialDataValidator(),
				FinancialDataQualityInspectorTool(),
				RealMarketDataFetcher()],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            
            
            max_execution_time=None,
            llm=LLM(
                model="openai/gpt-4o-mini",
                temperature=0.7,
                
            ),
            
        )
    
    @agent
    def alternative_data_intelligence_analyst(self) -> Agent:
        
        return Agent(
            config=self.agents_config["alternative_data_intelligence_analyst"],
            
            
            tools=[				AdditionalDataSourcesIntegratorTool()],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            
            
            max_execution_time=None,
            llm=LLM(
                model="openai/gpt-4o-mini",
                temperature=0.7,
                
            ),
            
        )
    

    
    @task
    def enhanced_multi_source_market_data_collection(self) -> Task:
        return Task(
            config=self.tasks_config["enhanced_multi_source_market_data_collection"],
            markdown=False,
            
            
        )
    
    @task
    def technical_analysis(self) -> Task:
        return Task(
            config=self.tasks_config["technical_analysis"],
            markdown=False,
            
            
        )
    
    @task
    def alternative_data_intelligence_analysis(self) -> Task:
        return Task(
            config=self.tasks_config["alternative_data_intelligence_analysis"],
            markdown=False,
            
            
        )
    
    @task
    def comprehensive_news_and_economic_analysis(self) -> Task:
        return Task(
            config=self.tasks_config["comprehensive_news_and_economic_analysis"],
            markdown=False,
            
            
        )
    
    @task
    def data_quality_validation(self) -> Task:
        return Task(
            config=self.tasks_config["data_quality_validation"],
            markdown=False,
            
            
        )
    
    @task
    def generate_investment_recommendation(self) -> Task:
        return Task(
            config=self.tasks_config["generate_investment_recommendation"],
            markdown=False,
            
            
        )
    
    @task
    def coordinate_market_analysis(self) -> Task:
        return Task(
            config=self.tasks_config["coordinate_market_analysis"],
            markdown=False,
            
            
        )
    

    @crew
    def crew(self) -> Crew:
        """Creates the AdvancedFinancialIntelligenceCenter crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            chat_llm=LLM(model="openai/gpt-4o-mini"),
        )


