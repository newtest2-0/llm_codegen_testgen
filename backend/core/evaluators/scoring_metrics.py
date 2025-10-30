"""
评分指标计算模块
实现BLEU4、ROUGE和pass@k等评估指标
"""
import nltk
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer

# 下载必要的NLTK数据
try:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('stopwords', quiet=True)
except:
    pass

logger = logging.getLogger(__name__)

class AdvancedScoringMetrics:
    """高级评分指标计算类"""
    
    def __init__(self):
        # 初始化ROUGE评分器，支持ROUGE-1, ROUGE-2, ROUGE-L
        self.rouge_scorer = rouge_scorer.RougeScorer(
            ['rouge1', 'rouge2', 'rougeL'], 
            use_stemmer=True
        )
    
    def calculate_bleu4(self, candidate: str, references: List[str]) -> float:
        """
        计算BLEU-4分数
        
        Args:
            candidate: 候选文本
            references: 参考文本列表
            
        Returns:
            BLEU-4分数 (0-1)
        """
        try:
            # 将文本分词
            candidate_tokens = nltk.word_tokenize(candidate.lower())
            
            # 将参考文本分词
            reference_tokens_list = [
                nltk.word_tokenize(ref.lower()) 
                for ref in references
            ]
            
            # 计算BLEU-4分数（4-gram）
            weights = (0.25, 0.25, 0.25, 0.25)  # 1-gram到4-gram权重均等
            smoothing = SmoothingFunction().method1
            
            bleu_score = sentence_bleu(
                reference_tokens_list, 
                candidate_tokens, 
                weights=weights,
                smoothing_function=smoothing
            )
            
            return bleu_score
            
        except Exception as e:
            logger.warning(f"BLEU-4计算失败: {e}")
            return 0.0
    
    def calculate_rouge(self, candidate: str, reference: str) -> Dict[str, float]:
        """
        计算ROUGE分数
        
        Args:
            candidate: 候选文本
            reference: 参考文本
            
        Returns:
            ROUGE分数字典
        """
        try:
            # 计算ROUGE分数
            scores = self.rouge_scorer.score(reference, candidate)
            
            # 提取主要ROUGE分数
            rouge_scores = {
                'rouge1': scores['rouge1'].fmeasure,
                'rouge2': scores['rouge2'].fmeasure,
                'rougeL': scores['rougeL'].fmeasure
            }
            
            return rouge_scores
            
        except Exception as e:
            logger.warning(f"ROUGE计算失败: {e}")
            return {'rouge1': 0.0, 'rouge2': 0.0, 'rougeL': 0.0}
    
    def calculate_pass_at_k(self, passed_tests: int, total_tests: int, k: int = 10) -> float:
        """
        计算pass@k分数
        
        Args:
            passed_tests: 通过的测试数
            total_tests: 总测试数
            k: k值，默认为10
            
        Returns:
            pass@k分数 (0-1)
        """
        try:
            # 如果没有测试，则返回0
            if total_tests == 0:
                return 0.0
                
            # 如果所有测试都通过，则返回1
            if passed_tests >= total_tests:
                return 1.0
            
            # 计算pass@k
            # pass@k = 1 - C(total_tests - passed_tests, k) / C(total_tests, k)
            import math
            
            if total_tests < k:
                # 如果总测试数小于k，则使用实际测试数
                k = total_tests
            
            # 计算组合数 C(n, k)
            def combination(n, k):
                if k > n or k < 0:
                    return 0
                if k == 0 or k == n:
                    return 1
                return math.factorial(n) / (math.factorial(k) * math.factorial(n - k))
            
            total_combinations = combination(total_tests, k)
            if total_combinations == 0:
                return 0.0
                
            failed_tests = total_tests - passed_tests
            failed_combinations = combination(failed_tests, k)
            
            pass_at_k = 1.0 - (failed_combinations / total_combinations)
            
            return max(0.0, min(1.0, pass_at_k))
            
        except Exception as e:
            logger.warning(f"pass@k计算失败: {e}")
            return 0.0
    
    def evaluate_generated_code(self, generated_code: str, reference_codes: List[str], 
                              passed_tests: int, total_tests: int) -> Dict[str, Any]:
        """
        综合评估生成的代码
        
        Args:
            generated_code: 生成的代码
            reference_codes: 参考代码列表
            passed_tests: 通过的测试数
            total_tests: 总测试数
            
        Returns:
            包含所有评分指标的字典
        """
        # 计算BLEU-4分数
        bleu4_score = self.calculate_bleu4(generated_code, reference_codes)
        
        # 计算ROUGE分数（使用第一个参考代码作为基准）
        rouge_scores = {}
        if reference_codes:
            rouge_scores = self.calculate_rouge(generated_code, reference_codes[0])
        
        # 计算pass@k分数
        pass_at_k_score = self.calculate_pass_at_k(passed_tests, total_tests, k=10)
        pass_at_1_score = self.calculate_pass_at_k(passed_tests, total_tests, k=1)
        
        return {
            'bleu4': bleu4_score,
            'rouge': rouge_scores,
            'pass_at_k': {
                'pass@1': pass_at_1_score,
                'pass@10': pass_at_k_score
            }
        }

# 兼容旧版本的函数
def calculate_bleu_score(candidate: str, references: List[str]) -> float:
    """兼容旧版本的BLEU计算函数"""
    scorer = AdvancedScoringMetrics()
    return scorer.calculate_bleu4(candidate, references)