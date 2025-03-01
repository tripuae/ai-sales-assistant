#!/usr/bin/env python3
"""
GPT-4o Model Performance Test for TripUAE Assistant

This script tests the GPT-4o model with tourism-specific scenarios
to validate improved conversational capabilities.
"""

import os
import json
import time
from dotenv import load_dotenv
import openai
from datetime import datetime

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Test scenarios - tourism and excursion related queries in Russian
TEST_SCENARIOS = [
    {
        "name": "Basic greeting",
        "messages": [
            {"role": "system", "content": "Вы — Мария, менеджер туристической компании TripUAE."},
            {"role": "user", "content": "Привет! Подскажите, какие экскурсии у вас есть в Дубае?"}
        ]
    },
    {
        "name": "Complex pricing inquiry",
        "messages": [
            {"role": "system", "content": "Вы — Мария, менеджер туристической компании TripUAE."},
            {"role": "user", "content": "Здравствуйте! Мы семья из 4 человек (2 взрослых, дети 7 и 10 лет). Хотели бы узнать про сафари в пустыне. Насколько это безопасно для детей и сколько стоит?"}
        ]
    },
    {
        "name": "Objection handling",
        "messages": [
            {"role": "system", "content": "Вы — Мария, менеджер туристической компании TripUAE."},
            {"role": "assistant", "content": "Экскурсия в Абу-Даби с посещением мечети Шейха Зайда стоит 680 AED с человека."},
            {"role": "user", "content": "Это довольно дорого. У вас есть варианты подешевле?"}
        ]
    },
    {
        "name": "Detailed itinerary request",
        "messages": [
            {"role": "system", "content": "Вы — Мария, менеджер туристической компании TripUAE."},
            {"role": "user", "content": "Расскажите подробнее, что входит в программу VIP-тура по Дубаю? Сколько длится экскурсия и что мы увидим?"}
        ]
    }
]

def run_tests():
    """Run all test scenarios and report results"""
    results = []
    total_time = 0
    
    print(f"\n=== GPT-4o PERFORMANCE TEST FOR TRIPUAE ASSISTANT ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print(f"Running scenario {i}/{len(TEST_SCENARIOS)}: {scenario['name']}...")
        
        try:
            # Time the response
            start_time = time.time()
            
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=scenario['messages'],
                temperature=0.7,
                max_tokens=800
            )
            
            elapsed = time.time() - start_time
            total_time += elapsed
            
            content = response.choices[0].message.content
            
            # Print truncated response
            print(f"✓ Response received in {elapsed:.2f}s")
            print(f"Sample: {content[:100]}...\n")
            
            results.append({
                "scenario": scenario["name"],
                "success": True,
                "time": elapsed,
                "response_length": len(content),
                "response_snippet": content[:100] + "..."
            })
            
        except Exception as e:
            print(f"✗ Error: {str(e)}\n")
            results.append({
                "scenario": scenario["name"],
                "success": False,
                "error": str(e)
            })
    
    # Print summary
    success_count = sum(1 for r in results if r["success"])
    print("\n=== TEST SUMMARY ===")
    print(f"Tests passed: {success_count}/{len(TEST_SCENARIOS)} ({success_count/len(TEST_SCENARIOS)*100:.1f}%)")
    
    if success_count > 0:
        avg_time = total_time / success_count
        print(f"Average response time: {avg_time:.2f}s")
    
    print("\nDetailed results:")
    for r in results:
        status = "✓ PASS" if r["success"] else "✗ FAIL"
        print(f"{status} - {r['scenario']}")
    
    # Save results to file
    with open("gpt4o_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\nResults saved to gpt4o_test_results.json")

if __name__ == "__main__":
    run_tests()
