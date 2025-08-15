#!/usr/bin/env python3
"""
Test script for specific subtopic generation
"""

import asyncio
import os
import sys

# Add backend to path
sys.path.append('backend')

async def test_specific_subtopics():
    """Test the improved content generation with specific subtopics"""
    
    # Sample educational text about Complex Numbers (similar to user's content)
    sample_text = """
    Complex Numbers
    
    Introduction and Motivation
    Complex numbers were developed to solve equations that have no real solutions, such as x² + 1 = 0. The need for complex numbers arose from the limitations of real numbers.
    
    Definition of Complex Numbers
    A complex number is a number in the form a + bi, where a and b are real numbers and i is the imaginary unit defined by i² = -1.
    
    The Imaginary Unit i
    The imaginary unit i is defined as the square root of -1. This allows us to extend the real number system to include solutions to previously unsolvable equations.
    
    Geometric Representation
    Complex numbers can be represented geometrically in the complex plane, where the real part is plotted on the x-axis and the imaginary part on the y-axis.
    
    Argand Diagram
    The Argand diagram is a graphical representation of complex numbers in the complex plane, named after Jean-Robert Argand.
    
    Modulus and Argument
    The modulus of a complex number z = a + bi is |z| = √(a² + b²), and the argument is the angle θ such that tan θ = b/a.
    
    Complex Conjugate
    The complex conjugate of z = a + bi is z̄ = a - bi. It has important properties in complex arithmetic.
    
    Polar Form
    Complex numbers can be expressed in polar form as z = r(cos θ + i sin θ), where r is the modulus and θ is the argument.
    
    Euler's Formula
    Euler's formula states that e^(iθ) = cos θ + i sin θ, providing a connection between exponential and trigonometric functions.
    
    De Moivre's Theorem
    De Moivre's theorem states that (cos θ + i sin θ)^n = cos(nθ) + i sin(nθ), useful for finding powers and roots of complex numbers.
    """
    
    try:
        from app.services.llm_service import LLMService
        
        print("Testing specific subtopic generation...")
        print("=" * 60)
        
        llm_service = LLMService()
        
        # Test content generation
        result = await llm_service.generate_educational_content(
            text=sample_text,
            topic="Complex Numbers"
        )
        
        print(f"Success: {result['success']}")
        print(f"Total items: {result['total_items']}")
        print(f"Processing time: {result['processing_time']:.2f}s")
        print(f"Main topic: {result['topic']}")
        
        print(f"\nGenerated {len(result['content_items'])} specific subtopics:")
        print("=" * 60)
        
        for i, item in enumerate(result['content_items'], 1):
            print(f"\n{i}. Topic: {item['topic']}")
            print(f"   Subtopic: {item['subtopic']}")
            print(f"   Content Length: {len(item['content'])} characters")
            print(f"   Content Preview: {item['content'][:100]}...")
            print("-" * 50)
        
        # Check if we have specific subtopics
        subtopics = [item['subtopic'] for item in result['content_items']]
        print(f"\nAll subtopics generated:")
        for i, subtopic in enumerate(subtopics, 1):
            print(f"  {i}. {subtopic}")
        
        # Check for specific vs broad subtopics
        specific_keywords = ['introduction', 'definition', 'imaginary', 'geometric', 'argand', 'modulus', 'conjugate', 'polar', 'euler', 'moivre', 'operations', 'venn', 'sets', 'logic']
        broad_keywords = ['basic', 'general', 'advanced', 'comprehensive', 'overview']
        
        specific_count = sum(1 for subtopic in subtopics if any(keyword in subtopic.lower() for keyword in specific_keywords))
        broad_count = sum(1 for subtopic in subtopics if any(keyword in subtopic.lower() for keyword in broad_keywords))
        
        print(f"\nSpecific subtopics: {specific_count}")
        print(f"Broad subtopics: {broad_count}")
        
        if specific_count > broad_count and len(result['content_items']) >= 5:
            print("\n✅ SUCCESS: Generated specific, concrete subtopics!")
            print("Each subtopic is focused and will have concise content.")
        else:
            print("\n⚠️  WARNING: May need more specific subtopics.")
        
        return result['success'] and len(result['content_items']) >= 5
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_specific_subtopics())
    if success:
        print("\n✅ Specific subtopic generation test passed!")
    else:
        print("\n❌ Specific subtopic generation test failed!")
