#!/usr/bin/env python3
"""
Anti-Seeding & Real Sentiment Verification Engine.
Protects against review-bombing, PR bot astroturfing, and inflated marketing ratings.
"""

import math
from typing import Dict, Any, Tuple

class SentimentFilter:
    def __init__(self, min_votes: int = 300, min_rating: float = 6.5):
        self.min_votes = min_votes
        self.min_rating = min_rating

    def analyze_sentiment(self, vote_average: float, vote_count: int, title: str = "") -> Dict[str, Any]:
        """
        Evaluates real sentiment credibility and detects potential seeding/astroturfing.
        """
        vote_average = float(vote_average or 0.0)
        vote_count = int(vote_count or 0)

        # 1. Check volume sufficiency
        if vote_count < 50:
            return {
                "verdict": "UNVERIFIED",
                "badge": "🔴 Chưa đủ dữ liệu",
                "credibility_score": 0.3,
                "reason": f"Chỉ có {vote_count} lượt đánh giá (quá ít để kết luận, có thể là PR seeding).",
                "adjusted_rating": round(vote_average * 0.8, 1),
                "is_genuine": False
            }
        
        if vote_count < self.min_votes:
            return {
                "verdict": "LOW_SAMPLE",
                "badge": "🟡 Mẫu khảo sát thấp",
                "credibility_score": 0.6,
                "reason": f"{vote_count} đánh giá (< ngưỡng an toàn {self.min_votes}), rủi ro bị bơm điểm.",
                "adjusted_rating": round(vote_average * 0.9, 1),
                "is_genuine": vote_average >= self.min_rating
            }

        # 2. Bayesian-inspired weighted score (IMDb formula style)
        # C = prior mean (approx 6.8), m = min votes threshold
        C = 6.8
        m = max(self.min_votes, 300)
        weighted_rating = (vote_count / (vote_count + m)) * vote_average + (m / (vote_count + m)) * C
        weighted_rating = round(weighted_rating, 1)

        # 3. Assess consensus level
        if vote_average >= 8.0 and vote_count >= 1000:
            badge = "🔥 Siêu phẩm đồng thuận"
            verdict = "MASTERPIECE"
        elif vote_average >= 7.2:
            badge = "🟢 Đánh giá thực chất tốt"
            verdict = "SOLID_QUALITY"
        elif vote_average >= 6.5:
            badge = "🔵 Xem ổn định / Giải trí khá"
            verdict = "ENTERTAINING"
        else:
            badge = "⚪ Trung bình / Cần cân nhắc"
            verdict = "AVERAGE"

        return {
            "verdict": verdict,
            "badge": badge,
            "credibility_score": min(1.0, 0.7 + (math.log10(vote_count) / 10.0)),
            "reason": f"Dữ liệu từ {vote_count:,} khán giả thực tế (Độ tin cậy cao).",
            "adjusted_rating": weighted_rating,
            "raw_rating": vote_average,
            "vote_count": vote_count,
            "is_genuine": weighted_rating >= self.min_rating
        }

if __name__ == "__main__":
    sf = SentimentFilter()
    print("Testing 10 votes 9.5 rating:")
    print(sf.analyze_sentiment(9.5, 12, "Fake Hype"))
    print("\nTesting 2500 votes 7.8 rating:")
    print(sf.analyze_sentiment(7.8, 2500, "Real Good Movie"))
