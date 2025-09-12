#!/usr/bin/env python3
"""
Test script for quiz generation functionality
"""

import asyncio
import sys
import os

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Set environment variables for testing
os.environ.setdefault('GEMINI_API_KEY', 'test_key')

try:
    from app.services.quiz_service import QuizService
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"📁 Backend path: {backend_path}")
    print(f"📁 Current working directory: {os.getcwd()}")
    sys.exit(1)

async def test_quiz_generation():
    """Test the quiz generation functionality"""
    print("🧪 Testing Quiz Generation Functionality")
    print("=" * 50)
    
    # Initialize the quiz service
    quiz_service = QuizService()
    
    # Test content (Urdu text)
    test_content = """
    مولوی نذیر احمد دہلوی اردو کے پہلے ناول نگار تھے۔ انہوں نے "مراۃ العروس" اور "توبۃ النصوح" جیسے مشہور ناول لکھے۔ 
    ان کا اصل نام دیوان نذیر احمد تھا۔ وہ 1831 میں دہلی میں پیدا ہوئے۔ انہوں نے عربی، فارسی اور اردو کی تعلیم حاصل کی۔
    ان کے ناولوں میں خواتین کی تعلیم اور سماجی اصلاح کے موضوعات شامل ہیں۔
    """
    
    test_topic = "خلاصہ"
    test_chapter = "ٹیسٹ یونٹ PTB2:6"
    
    print(f"📝 Test Content: {test_content[:100]}...")
    print(f"📚 Topic: {test_topic}")
    print(f"📖 Chapter: {test_chapter}")
    print()
    
    try:
        # Test quiz generation
        print("🎯 Generating quiz questions...")
        result = await quiz_service.generate_quiz_from_text(
            text=test_content,
            topic=test_topic,
            chapter=test_chapter,
            num_questions=5,
            language="urdu"
        )
        
        if result['success']:
            print("✅ Quiz generation successful!")
            print(f"📊 Total questions: {result['total_questions']}")
            print(f"⏱️  Processing time: {result['processing_time']:.2f} seconds")
            print()
            
            # Display questions
            for i, question in enumerate(result['questions'], 1):
                print(f"❓ Question {i}:")
                print(f"   Q: {question['question']}")
                print(f"   A: {question['option_1']}")
                print(f"   B: {question['option_2']}")
                print(f"   C: {question['option_3']}")
                print(f"   D: {question['option_4']}")
                print(f"   Correct: Option {question['correct_option']}")
                print(f"   Explanation: {question['explanation']}")
                print()
            
            # Test Excel generation
            print("📊 Generating Excel file...")
            excel_result = await quiz_service.generate_excel_file(
                questions=result['questions'],
                topic=test_topic,
                chapter=test_chapter
            )
            
            if excel_result['success']:
                print("✅ Excel file generated successfully!")
                print(f"📁 Filename: {excel_result['filename']}")
                print(f"📁 File path: {excel_result['file_path']}")
                print(f"🔗 Download URL: {excel_result['file_url']}")
                print(f"📊 Questions in Excel: {excel_result['total_questions']}")
                
                # Check if file exists
                if os.path.exists(excel_result['file_path']):
                    file_size = os.path.getsize(excel_result['file_path'])
                    print(f"📏 File size: {file_size} bytes")
                else:
                    print("⚠️  File not found on disk")
                
            else:
                print("❌ Excel generation failed!")
                print(f"🚨 Error: {excel_result.get('error', 'Unknown error')}")
                
        else:
            print("❌ Quiz generation failed!")
            print(f"🚨 Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_quiz_generation())
