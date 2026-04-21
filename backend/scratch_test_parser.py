from core.parser.kotlin_parser import parse_kotlin_code, generic_extract_metadata

test_kotlin = """
package com.example.app

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import retrofit2.Retrofit

/**
 * This is a sample class to test the parser.
 * It handles the main UI logic.
 */
@ContentView(R.layout.activity_main)
class MainActivity : AppCompatActivity() {

    private lateinit var retrofit: Retrofit

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        setupNetwork()
    }

    @Inject
    fun setupNetwork() {
        // network logic here
    }
}
"""

print("--- Testing Kotlin Parser ---")
meta = parse_kotlin_code(test_kotlin)
print(f"Package: {meta.get('package')}")
print(f"Line Count: {meta.get('line_count')}")
print(f"Keywords: {meta.get('keywords')}")
print(f"Annotations: {meta.get('annotations')}")
print(f"Summary: {meta.get('summary_comment')}")

test_python = """
import os

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
    
    def connect(self):
        print(f"Connecting to {self.db_path}")

def main():
    db = Database("test.db")
    db.connect()
"""

print("\n--- Testing Generic Parser ---")
meta_gen = generic_extract_metadata("database.py", test_python)
print(f"Line Count: {meta_gen.get('line_count')}")
print(f"Keywords: {meta_gen.get('keywords')}")
print(f"File Size: {meta_gen.get('file_size')}")
