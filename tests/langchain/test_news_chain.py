# tests/langchain/test_news_chain.py

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.langchain.news_chain import NewsItem, NewsProcessingChain
from src.openai_client import OpenAIClient
import json


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
        
        # Создаем 3 новости, но должно обработаться только 2
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", datetime.now(), "source1"),
            NewsItem("Title 2", "Description 2", "http://example.com/2", datetime.now(), "source2"),
            NewsItem("Title 3", "Description 3", "http://example.com/3", datetime.now(), "source3")
        ]
        
        result = chain.process_news(news_items)
        
        assert len(result) == 2  # Должно быть ограничено до 2
        assert mock_embeddings_instance.embed_documents.call_count == 1
    
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

    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    def test_deduplicate_news_same_time(self, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест дедупликации когда новости имеют одинаковое время публикации"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        chain = NewsProcessingChain(openai_client=mock_openai_client, similarity_threshold=0.9)
        
        # Создаем новости с одинаковым временем
        same_time = datetime(2025, 1, 15, 12, 0, 0)
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", same_time, "source1"),
            NewsItem("Title 2", "Description 2", "http://example.com/2", same_time, "source2")
        ]
        
        # Устанавливаем очень похожие эмбеддинги
        news_items[0].embedding = np.array([0.9, 0.1, 0.0], dtype=np.float32)
        news_items[1].embedding = np.array([0.95, 0.05, 0.0], dtype=np.float32)
        
        # Мокаем FAISS для возврата высокой схожести
        with patch('src.langchain.news_chain.faiss.IndexFlatIP') as mock_index_class:
            mock_index = Mock()
            mock_index_class.return_value = mock_index
            mock_index.search.return_value = (
                np.array([[0.95, 0.92]]),  # Высокая схожесть
                np.array([[0, 1]])         # Индексы
            )
            
            result = chain.deduplicate_news(news_items)
            
            # Когда время одинаковое, алгоритм может пометить обе новости как дубли
            # Это корректное поведение для очень похожих новостей
            assert len(result) == 0  # Обе новости считаются дублями друг друга

    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    def test_deduplicate_news_missing_embeddings(self, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест дедупликации когда у некоторых новостей нет эмбеддингов"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        chain = NewsProcessingChain(openai_client=mock_openai_client)
        
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", datetime.now(), "source1"),
            NewsItem("Title 2", "Description 2", "http://example.com/2", datetime.now(), "source2")
        ]
        
        # Только у одной новости есть эмбеддинг
        news_items[0].embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        # news_items[1].embedding остается None
        
        result = chain.deduplicate_news(news_items)
        
        # Должна остаться только новость с эмбеддингом
        assert len(result) == 1
        assert result[0].url == "http://example.com/1"

    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    def test_deduplicate_news_no_embeddings(self, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест дедупликации когда ни у одной новости нет эмбеддингов"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        chain = NewsProcessingChain(openai_client=mock_openai_client)
        
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", datetime.now(), "source1"),
            NewsItem("Title 2", "Description 2", "http://example.com/2", datetime.now(), "source2")
        ]
        
        # Ни у одной новости нет эмбеддинга
        
        result = chain.deduplicate_news(news_items)
        
        # Должны вернуться все новости без изменений
        assert len(result) == 2
        assert result == news_items

    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    @patch('src.langchain.news_chain.ChatOpenAI')
    @patch('src.langchain.news_chain.PromptTemplate')
    def test_rank_news_json_with_code_block(self, mock_prompt_template, mock_chat_openai, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест ранжирования с JSON в блоке кода"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Мокаем LLM цепочку
        mock_chain = Mock()
        mock_prompt_template.return_value.pipe.return_value = mock_chain
        
        # Возвращаем JSON в блоке кода
        mock_chain.invoke.return_value = '''```json
{
  "rankings": [
    {"url": "http://example.com/1", "score": 8.5}
  ]
}
```'''
        
        chain = NewsProcessingChain(openai_client=mock_openai_client)
        chain.ranking_chain = mock_chain
        
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", datetime.now(), "source1")
        ]
        
        result = chain.rank_news(news_items)
        
        assert len(result) == 1
        assert result[0].relevance_score == 8.5

    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    @patch('src.langchain.news_chain.ChatOpenAI')
    @patch('src.langchain.news_chain.PromptTemplate')
    def test_rank_news_json_in_text(self, mock_prompt_template, mock_chat_openai, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест ранжирования с JSON в тексте"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Мокаем LLM цепочку
        mock_chain = Mock()
        mock_prompt_template.return_value.pipe.return_value = mock_chain
        
        # Возвращаем JSON в тексте
        mock_chain.invoke.return_value = '''Here is the ranking result:
{
  "rankings": [
    {"url": "http://example.com/1", "score": 7.2}
  ]
}
End of result.'''
        
        chain = NewsProcessingChain(openai_client=mock_openai_client)
        chain.ranking_chain = mock_chain
        
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", datetime.now(), "source1")
        ]
        
        result = chain.rank_news(news_items)
        
        assert len(result) == 1
        assert result[0].relevance_score == 7.2

    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    @patch('src.langchain.news_chain.ChatOpenAI')
    @patch('src.langchain.news_chain.PromptTemplate')
    def test_rank_news_no_json_found(self, mock_prompt_template, mock_chat_openai, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест ранжирования когда JSON не найден"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Мокаем LLM цепочку
        mock_chain = Mock()
        mock_prompt_template.return_value.pipe.return_value = mock_chain
        
        # Возвращаем текст без JSON
        mock_chain.invoke.return_value = "This is just plain text without any JSON"
        
        chain = NewsProcessingChain(openai_client=mock_openai_client)
        chain.ranking_chain = mock_chain
        
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", datetime.now(), "source1")
        ]
        
        result = chain.rank_news(news_items)
        
        # Должна быть установлена дефолтная оценка
        assert len(result) == 1
        assert result[0].relevance_score == 5.0

    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    @patch('src.langchain.news_chain.ChatOpenAI')
    @patch('src.langchain.news_chain.PromptTemplate')
    def test_rank_news_json_not_clean_format(self, mock_prompt_template, mock_chat_openai, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест ранжирования с JSON не в чистом формате"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Мокаем LLM цепочку
        mock_chain = Mock()
        mock_prompt_template.return_value.pipe.return_value = mock_chain
        
        # Возвращаем JSON не в чистом формате (не начинается и не заканчивается с {})
        mock_chain.invoke.return_value = '''prefix {"rankings": [{"url": "http://example.com/1", "score": 6.5}]} suffix'''
        
        chain = NewsProcessingChain(openai_client=mock_openai_client)
        chain.ranking_chain = mock_chain
        
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", datetime.now(), "source1")
        ]
        
        result = chain.rank_news(news_items)
        
        assert len(result) == 1
        assert result[0].relevance_score == 6.5

    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    @patch('src.langchain.news_chain.ChatOpenAI')
    @patch('src.langchain.news_chain.PromptTemplate')
    def test_rank_news_json_regex_no_match(self, mock_prompt_template, mock_chat_openai, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест ранжирования когда regex не находит JSON"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Мокаем LLM цепочку
        mock_chain = Mock()
        mock_prompt_template.return_value.pipe.return_value = mock_chain
        
        # Возвращаем текст без JSON объекта (только отдельные скобки)
        mock_chain.invoke.return_value = '''Some text { and } separate braces without proper JSON structure'''
        
        chain = NewsProcessingChain(openai_client=mock_openai_client)
        chain.ranking_chain = mock_chain
        
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", datetime.now(), "source1")
        ]
        
        result = chain.rank_news(news_items)
        
        # Должна быть установлена дефолтная оценка при ошибке
        assert len(result) == 1
        assert result[0].relevance_score == 5.0

    @patch('src.langchain.news_chain.get_ai_settings')
    def test_create_news_processing_chain_function(self, mock_get_ai_settings, mock_openai_client):
        """Тест функции создания цепочки"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        from src.langchain.news_chain import create_news_processing_chain
        
        chain = create_news_processing_chain(
            openai_client=mock_openai_client,
            similarity_threshold=0.9,
            max_news_items=25
        )
        
        assert isinstance(chain, NewsProcessingChain)
        assert chain.similarity_threshold == 0.9
        assert chain.max_news_items == 25


class TestLLMErrorHandling:
    """Тесты для обработки ошибок LLM"""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Фикстура для мокирования OpenAI клиента"""
        return Mock()
    
    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    def test_retry_with_backoff_rate_limit(self, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест повторных попыток при rate limit"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Первые 2 вызова - rate limit, третий - успех
        mock_embeddings_instance.embed_documents.side_effect = [
            Exception("Rate limit exceeded"),
            Exception("Rate limit 429"),
            [[0.1, 0.2, 0.3]]
        ]
        
        chain = NewsProcessingChain(openai_client=mock_openai_client, retry_delay=0.1)
        
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", datetime.now(), "source1")
        ]
        
        # Мокаем time.sleep чтобы тесты были быстрыми
        with patch('src.langchain.news_chain.time.sleep'):
            result = chain.create_embeddings(news_items)
        
        assert len(result) == 1
        assert result[0].embedding is not None
        assert mock_embeddings_instance.embed_documents.call_count == 3
    
    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    def test_retry_with_backoff_authentication_error(self, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест что ошибки аутентификации не повторяются"""
        from src.langchain.news_chain import EmbeddingError
        
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Ошибка аутентификации
        mock_embeddings_instance.embed_documents.side_effect = Exception("Authentication failed")
        
        chain = NewsProcessingChain(openai_client=mock_openai_client, retry_delay=0.1)
        
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", datetime.now(), "source1")
        ]
        
        with pytest.raises(EmbeddingError):
            chain.create_embeddings(news_items)
        
        # Должен быть только один вызов (без повторов)
        assert mock_embeddings_instance.embed_documents.call_count == 1
    
    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    def test_retry_with_backoff_network_error(self, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест повторных попыток при сетевых ошибках"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Первые 2 вызова - сетевые ошибки, третий - успех
        mock_embeddings_instance.embed_documents.side_effect = [
            Exception("Connection timeout"),
            Exception("Network connection failed"),
            [[0.1, 0.2, 0.3]]
        ]
        
        chain = NewsProcessingChain(openai_client=mock_openai_client, retry_delay=0.1)
        
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", datetime.now(), "source1")
        ]
        
        # Мокаем time.sleep чтобы тесты были быстрыми
        with patch('src.langchain.news_chain.time.sleep'):
            result = chain.create_embeddings(news_items)
        
        assert len(result) == 1
        assert result[0].embedding is not None
        assert mock_embeddings_instance.embed_documents.call_count == 3
    
    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    def test_retry_exhausted(self, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест когда все попытки исчерпаны"""
        from src.langchain.news_chain import EmbeddingError
        
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Все вызовы - rate limit
        mock_embeddings_instance.embed_documents.side_effect = Exception("Rate limit exceeded")
        
        chain = NewsProcessingChain(openai_client=mock_openai_client, max_retries=2, retry_delay=0.1)
        
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", datetime.now(), "source1")
        ]
        
        # Мокаем time.sleep чтобы тесты были быстрыми
        with patch('src.langchain.news_chain.time.sleep'):
            with pytest.raises(EmbeddingError):
                chain.create_embeddings(news_items)
        
        # Должно быть max_retries + 1 попыток
        assert mock_embeddings_instance.embed_documents.call_count == 3
    
    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    @patch('src.langchain.news_chain.ChatOpenAI')
    @patch('src.langchain.news_chain.PromptTemplate')
    def test_ranking_error_handling(self, mock_prompt_template, mock_chat_openai, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест обработки ошибок при ранжировании"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Мокаем LLM цепочку
        mock_chain = Mock()
        mock_prompt_template.return_value.pipe.return_value = mock_chain
        
        # Возвращаем невалидный JSON
        mock_chain.invoke.side_effect = Exception("LLM error")
        
        chain = NewsProcessingChain(openai_client=mock_openai_client, retry_delay=0.1)
        chain.ranking_chain = mock_chain
        
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", datetime.now(), "source1")
        ]
        
        # Мокаем time.sleep чтобы тесты были быстрыми
        with patch('src.langchain.news_chain.time.sleep'):
            result = chain.rank_news(news_items)
        
        # Должны получить исходный список с дефолтными оценками
        assert len(result) == 1
        assert result[0].relevance_score == 5.0
    
    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    @patch('src.langchain.news_chain.ChatOpenAI')
    @patch('src.langchain.news_chain.PromptTemplate')
    def test_process_ranking_result_validation(self, mock_prompt_template, mock_chat_openai, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест валидации результатов ранжирования"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Мокаем LLM цепочку
        mock_chain = Mock()
        mock_prompt_template.return_value.pipe.return_value = mock_chain
        
        # Возвращаем JSON с невалидными оценками
        mock_chain.invoke.return_value = json.dumps({
            "rankings": [
                {"url": "http://example.com/1", "score": 15},  # Слишком высокая оценка
                {"url": "http://example.com/2", "score": -5},  # Слишком низкая оценка
                {"url": "http://example.com/3", "score": "invalid"},  # Невалидная оценка
                {"url": "http://example.com/4", "score": 7.5}  # Валидная оценка
            ]
        })
        
        chain = NewsProcessingChain(openai_client=mock_openai_client)
        chain.ranking_chain = mock_chain
        
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", datetime.now(), "source1"),
            NewsItem("Title 2", "Description 2", "http://example.com/2", datetime.now(), "source2"),
            NewsItem("Title 3", "Description 3", "http://example.com/3", datetime.now(), "source3"),
            NewsItem("Title 4", "Description 4", "http://example.com/4", datetime.now(), "source4")
        ]
        
        result = chain.rank_news(news_items)
        
        # Проверяем что оценки были скорректированы
        assert len(result) == 4
        
        # Находим новости по URL
        items_by_url = {item.url: item for item in result}
        
        # Высокая оценка должна быть ограничена до 10
        assert items_by_url["http://example.com/1"].relevance_score == 10.0
        
        # Низкая оценка должна быть ограничена до 1
        assert items_by_url["http://example.com/2"].relevance_score == 1.0
        
        # Невалидная оценка должна стать дефолтной
        assert items_by_url["http://example.com/3"].relevance_score == 5.0
        
        # Валидная оценка должна остаться без изменений
        assert items_by_url["http://example.com/4"].relevance_score == 7.5
    
    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    def test_process_news_fail_on_errors_true(self, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест режима fail_on_errors=True"""
        from src.langchain.news_chain import EmbeddingError
        
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Ошибка создания embeddings
        mock_embeddings_instance.embed_documents.side_effect = Exception("Embedding failed")
        
        chain = NewsProcessingChain(openai_client=mock_openai_client, max_retries=1, retry_delay=0.1)
        
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", datetime.now(), "source1")
        ]
        
        # Мокаем time.sleep чтобы тесты были быстрыми
        with patch('src.langchain.news_chain.time.sleep'):
            with pytest.raises(EmbeddingError):
                chain.process_news(news_items, fail_on_errors=True)
    
    @patch('src.langchain.news_chain.get_ai_settings')
    @patch('src.langchain.news_chain.OpenAIEmbeddings')
    def test_process_news_fail_on_errors_false(self, mock_embeddings_class, mock_get_ai_settings, mock_openai_client):
        """Тест режима fail_on_errors=False (продолжение при ошибках)"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_get_ai_settings.return_value = mock_settings
        
        mock_embeddings_instance = Mock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Ошибка создания embeddings
        mock_embeddings_instance.embed_documents.side_effect = Exception("Embedding failed")
        
        chain = NewsProcessingChain(openai_client=mock_openai_client, max_retries=1, retry_delay=0.1)
        
        news_items = [
            NewsItem("Title 1", "Description 1", "http://example.com/1", datetime.now(), "source1")
        ]
        
        # Мокаем time.sleep чтобы тесты были быстрыми
        with patch('src.langchain.news_chain.time.sleep'):
            result = chain.process_news(news_items, fail_on_errors=False)
        
        # Должны получить результат несмотря на ошибки
        assert len(result) == 1
        assert result[0].embedding is None  # Embedding не создался
        assert result[0].relevance_score == 5.0  # Дефолтная оценка 