# tests/langchain/test_news_chain.py

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.langchain.news_chain import NewsItem, NewsProcessingChain
from src.openai_client import OpenAIClient


class TestNewsItem:
    """Тесты для класса NewsItem"""
    
    def test_news_item_creation(self):
        """Тест создания объекта NewsItem"""
        news_item = NewsItem(
            title="Test News",
            description="Test Description",
            url="https://example.com/test",
            published_at=datetime(2025, 1, 15, 10, 0, 0),
            source="test.com"
        )
        
        assert news_item.title == "Test News"
        assert news_item.description == "Test Description"
        assert news_item.url == "https://example.com/test"
        assert news_item.published_at == datetime(2025, 1, 15, 10, 0, 0)
        assert news_item.source == "test.com"
        assert news_item.category is None
        assert news_item.embedding is None
        assert news_item.relevance_score == 5.0
        assert news_item.is_duplicate is False
        assert news_item.duplicate_of is None
        assert news_item.similarity_score == 0.0
    
    def test_news_item_to_dict(self):
        """Тест преобразования в словарь"""
        news_item = NewsItem(
            title="Test News",
            description="Test Description",
            url="https://example.com/test",
            published_at=datetime(2025, 1, 15, 10, 0, 0),
            source="test.com",
            category="technology"
        )
        
        # Устанавливаем дополнительные поля после создания
        news_item.relevance_score = 8.5
        news_item.is_duplicate = True
        news_item.duplicate_of = "https://example.com/original"
        news_item.similarity_score = 0.95
        
        result = news_item.to_dict()
        
        assert result["title"] == "Test News"
        assert result["description"] == "Test Description"
        assert result["url"] == "https://example.com/test"
        assert result["published_at"] == "2025-01-15T10:00:00"
        assert result["source"] == "test.com"
        assert result["category"] == "technology"
        assert result["relevance_score"] == 8.5
        assert result["is_duplicate"] is True
        assert result["duplicate_of"] == "https://example.com/original"
        assert result["similarity_score"] == 0.95
    
    def test_get_content_for_embedding(self):
        """Тест получения контента для эмбеддинга"""
        news_item = NewsItem(
            title="Test News",
            description="Test Description",
            url="https://example.com/test",
            published_at=datetime(2025, 1, 15, 10, 0, 0),
            source="test.com",
            category="technology"
        )
        
        content = news_item.get_content_for_embedding()
        expected = "Test News Test Description technology"
        assert content == expected
    
    def test_get_content_for_ranking(self):
        """Тест получения контента для ранжирования"""
        news_item = NewsItem(
            title="Test News",
            description="Test Description",
            url="https://example.com/test",
            published_at=datetime(2025, 1, 15, 10, 0, 0),
            source="test.com",
            category="technology"
        )
        
        content = news_item.get_content_for_ranking()
        expected = "Заголовок: Test News\nОписание: Test Description\nИсточник: test.com\nКатегория: technology"
        assert content == expected
    
    def test_get_content_for_ranking_no_category(self):
        """Тест получения контента для ранжирования без категории"""
        news_item = NewsItem(
            title="Test News",
            description="Test Description",
            url="https://example.com/test",
            published_at=datetime(2025, 1, 15, 10, 0, 0),
            source="test.com"
        )
        
        content = news_item.get_content_for_ranking()
        expected = "Заголовок: Test News\nОписание: Test Description\nИсточник: test.com"
        assert content == expected


class TestNewsProcessingChain:
    """Тесты для класса NewsProcessingChain"""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Фикстура для мока OpenAI клиента"""
        return Mock()
    
    @pytest.fixture
    def sample_news_items(self):
        """Фикстура с образцами новостей"""
        return [
            NewsItem(
                title="AI Revolution",
                description="AI is changing the world",
                url="https://example.com/ai-revolution",
                published_at=datetime(2025, 1, 15, 10, 0, 0),
                source="tech.com",
                category="technology"
            ),
            NewsItem(
                title="Market News",
                description="Stock market updates",
                url="https://example.com/market-news",
                published_at=datetime(2025, 1, 15, 11, 0, 0),
                source="finance.com",
                category="business"
            ),
            NewsItem(
                title="AI News",
                description="Latest AI developments",
                url="https://example.com/ai-news",
                published_at=datetime(2025, 1, 15, 12, 0, 0),
                source="ai.com",
                category="technology"
            )
        ]
    
    @patch('src.langchain.news_chain.get_ai_settings')
    def test_chain_initialization(self, mock_get_ai_settings, mock_openai_client):
        """Тест инициализации цепочки"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        chain = NewsProcessingChain(openai_client=mock_openai_client)
        
        assert chain.openai_client == mock_openai_client
        assert chain.similarity_threshold == 0.85
        assert chain.max_news_items == 50
        assert chain.embeddings is not None
        assert chain.ranking_chain is not None
    
    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    def test_create_embeddings_success(self, mock_embeddings_class, mock_get_ai_settings, mock_openai_client, sample_news_items):
        """Тест успешного создания эмбеддингов"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        # Мокаем класс эмбеддингов
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Мокаем результат эмбеддингов
        mock_embeddings = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ]
        mock_embeddings_instance.embed_documents.return_value = mock_embeddings
        
        chain = NewsProcessingChain(openai_client=mock_openai_client)
        
        result = chain.create_embeddings(sample_news_items)
        
        assert len(result) == 3
        for i, item in enumerate(result):
            assert item.embedding is not None
            assert isinstance(item.embedding, np.ndarray)
            assert item.embedding.dtype == np.float32
            np.testing.assert_array_equal(item.embedding, np.array(mock_embeddings[i], dtype=np.float32))
        
        # Проверяем что вызов был сделан с правильными текстами
        expected_texts = [item.get_content_for_embedding() for item in sample_news_items]
        mock_embeddings_instance.embed_documents.assert_called_once_with(expected_texts)
    
    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    def test_create_embeddings_failure(self, mock_embeddings_class, mock_get_ai_settings, mock_openai_client, sample_news_items):
        """Тест обработки ошибки при создании эмбеддингов"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        # Мокаем класс эмбеддингов
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Мокаем ошибку
        mock_embeddings_instance.embed_documents.side_effect = Exception("OpenAI API error")
        
        chain = NewsProcessingChain(openai_client=mock_openai_client)
        
        with pytest.raises(Exception, match="OpenAI API error"):
            chain.create_embeddings(sample_news_items)
    
    @patch('src.langchain.news_chain.get_ai_settings')
    def test_deduplicate_news_empty_list(self, mock_get_ai_settings, mock_openai_client):
        """Тест дедупликации пустого списка"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        chain = NewsProcessingChain(openai_client=mock_openai_client)
        
        result = chain.deduplicate_news([])
        assert result == []
    
    @patch('src.langchain.news_chain.get_ai_settings')
    def test_deduplicate_news_no_embeddings(self, mock_get_ai_settings, mock_openai_client, sample_news_items):
        """Тест дедупликации новостей без эмбеддингов"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        chain = NewsProcessingChain(openai_client=mock_openai_client)
        
        result = chain.deduplicate_news(sample_news_items)
        assert result == sample_news_items  # Должен вернуть исходный список
    
    @patch('src.langchain.news_chain.get_ai_settings')
    def test_deduplicate_news_with_duplicates(self, mock_get_ai_settings, mock_openai_client):
        """Тест дедупликации с обнаружением дублей"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        chain = NewsProcessingChain(openai_client=mock_openai_client, similarity_threshold=0.8)
        
        # Создаем новости с эмбеддингами
        news1 = NewsItem(
            title="AI News",
            description="AI development",
            url="https://example.com/1",
            published_at=datetime(2025, 1, 15, 10, 0, 0),
            source="source1.com"
        )
        news1.embedding = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        
        news2 = NewsItem(
            title="Similar AI News",
            description="Similar AI development",
            url="https://example.com/2",
            published_at=datetime(2025, 1, 15, 11, 0, 0),  # Позже
            source="source2.com"
        )
        news2.embedding = np.array([0.9, 0.1, 0.1], dtype=np.float32)  # Очень похожий
        
        news3 = NewsItem(
            title="Different News",
            description="Completely different topic",
            url="https://example.com/3",
            published_at=datetime(2025, 1, 15, 12, 0, 0),
            source="source3.com"
        )
        news3.embedding = np.array([0.0, 1.0, 0.0], dtype=np.float32)  # Совсем другой
        
        news_items = [news1, news2, news3]
        
        result = chain.deduplicate_news(news_items)
        
        # Должно остаться 2 новости (одна из похожих будет удалена)
        assert len(result) == 2
        
        # Проверяем что более поздняя новость отмечена как дубль
        unique_urls = {item.url for item in result}
        assert "https://example.com/1" in unique_urls  # Оригинал остается
        assert "https://example.com/3" in unique_urls  # Разная новость остается
        
        # Проверяем что news2 отмечена как дубль
        assert news2.is_duplicate is True
        assert news2.duplicate_of == news1.url
        assert news2.similarity_score > 0.8
    
    @patch('src.langchain.news_chain.get_ai_settings')
    def test_rank_news_empty_list(self, mock_get_ai_settings, mock_openai_client):
        """Тест ранжирования пустого списка"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        chain = NewsProcessingChain(openai_client=mock_openai_client)
        
        result = chain.rank_news([])
        assert result == []
    
    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.ChatOpenAI')
    @patch('src.langchain.news_chain.PromptTemplate')
    def test_rank_news_success(self, mock_prompt_template, mock_chat_openai, mock_get_ai_settings, mock_openai_client, sample_news_items):
        """Тест успешного ранжирования новостей"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        # Мокаем LLM цепочку
        mock_chain = Mock()
        mock_llm_response = '''
        {
            "rankings": [
                {"url": "https://example.com/ai-news", "score": 9, "reasoning": "High tech impact"},
                {"url": "https://example.com/market-news", "score": 6, "reasoning": "Medium business impact"},
                {"url": "https://example.com/ai-revolution", "score": 8, "reasoning": "High innovation impact"}
            ]
        }
        '''
        mock_chain.invoke.return_value = mock_llm_response
        
        # Мокаем создание цепочки
        with patch.object(NewsProcessingChain, '_create_ranking_chain', return_value=mock_chain):
            chain = NewsProcessingChain(openai_client=mock_openai_client)
            
            result = chain.rank_news(sample_news_items)
            
            assert len(result) == 3
            
            # Проверяем что новости отсортированы по убыванию оценки
            assert result[0].url == "https://example.com/ai-news"
            assert result[0].relevance_score == 9
            assert result[1].url == "https://example.com/ai-revolution"
            assert result[1].relevance_score == 8
            assert result[2].url == "https://example.com/market-news"
            assert result[2].relevance_score == 6
    
    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.ChatOpenAI')
    @patch('src.langchain.news_chain.PromptTemplate')
    def test_rank_news_llm_failure(self, mock_prompt_template, mock_chat_openai, mock_get_ai_settings, mock_openai_client, sample_news_items):
        """Тест обработки ошибки LLM при ранжировании"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        # Мокаем LLM цепочку с ошибкой
        mock_chain = Mock()
        mock_chain.invoke.side_effect = Exception("LLM error")
        
        # Мокаем создание цепочки
        with patch.object(NewsProcessingChain, '_create_ranking_chain', return_value=mock_chain):
            chain = NewsProcessingChain(openai_client=mock_openai_client)
            
            result = chain.rank_news(sample_news_items)
            
            # Должен вернуть исходный список с дефолтными оценками
            assert len(result) == 3
            for item in result:
                assert item.relevance_score == 5.0
    
    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.ChatOpenAI')
    @patch('src.langchain.news_chain.PromptTemplate')
    def test_rank_news_invalid_json(self, mock_prompt_template, mock_chat_openai, mock_get_ai_settings, mock_openai_client, sample_news_items):
        """Тест обработки невалидного JSON от LLM"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        # Мокаем LLM цепочку с невалидным JSON
        mock_chain = Mock()
        mock_chain.invoke.return_value = "Invalid JSON response"
        
        # Мокаем создание цепочки
        with patch.object(NewsProcessingChain, '_create_ranking_chain', return_value=mock_chain):
            chain = NewsProcessingChain(openai_client=mock_openai_client)
            
            result = chain.rank_news(sample_news_items)
            
            # Должен вернуть исходный список с дефолтными оценками
            assert len(result) == 3
            for item in result:
                assert item.relevance_score == 5.0
    
    @patch('src.langchain.news_chain.get_ai_settings')
    def test_process_news_empty_list(self, mock_get_ai_settings, mock_openai_client):
        """Тест обработки пустого списка новостей"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        chain = NewsProcessingChain(openai_client=mock_openai_client)
        
        result = chain.process_news([])
        assert result == []
    
    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    def test_process_news_limit_items(self, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест ограничения количества новостей"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        # Мокаем эмбеддинги - делаем их очень разными чтобы избежать дедупликации
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        mock_embeddings_instance.embed_documents.return_value = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
        
        chain = NewsProcessingChain(openai_client=mock_openai_client, max_news_items=2)
        
        # Создаем 3 новости
        news_items = [
            NewsItem(title=f"News {i}", description=f"Description {i}", url=f"https://example.com/{i}",
                    published_at=datetime(2025, 1, 15, 10, 0, 0), source="test.com")
            for i in range(3)
        ]
        
        result = chain.process_news(news_items)
        
        # Должно остаться только 2 новости
        assert len(result) == 2
    
    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    @patch('src.langchain.news_chain.ChatOpenAI')
    @patch('src.langchain.news_chain.PromptTemplate')
    def test_process_news_with_custom_criteria(self, mock_prompt_template, mock_chat_openai, mock_embeddings_class, mock_get_ai_settings, mock_openai_client, sample_news_items):
        """Тест обработки новостей с кастомными критериями"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        # Мокаем эмбеддинги - делаем их очень разными чтобы избежать дедупликации
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        mock_embeddings_instance.embed_documents.return_value = [
            [1.0, 0.0, 0.0],  # Совершенно разные векторы
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ]
        
        # Мокаем LLM цепочку
        mock_chain = Mock()
        mock_llm_response = '''
        {
            "rankings": [
                {"url": "https://example.com/ai-news", "score": 9, "reasoning": "High tech impact"},
                {"url": "https://example.com/market-news", "score": 6, "reasoning": "Medium business impact"},
                {"url": "https://example.com/ai-revolution", "score": 8, "reasoning": "High innovation impact"}
            ]
        }
        '''
        mock_chain.invoke.return_value = mock_llm_response
        
        # Мокаем создание цепочки
        with patch.object(NewsProcessingChain, '_create_ranking_chain', return_value=mock_chain):
            chain = NewsProcessingChain(openai_client=mock_openai_client)
            
            custom_criteria = "Фокус на технологические инновации"
            result = chain.process_news(sample_news_items, ranking_criteria=custom_criteria)
            
            assert len(result) == 3
            
            # Проверяем что кастомные критерии были переданы в LLM
            mock_chain.invoke.assert_called_once()
            call_args = mock_chain.invoke.call_args[0][0]
            assert call_args["criteria"] == custom_criteria 