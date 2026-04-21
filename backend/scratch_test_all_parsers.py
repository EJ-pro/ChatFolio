from core.parser.factory import get_parser_result
import textwrap

test_cases = [
    ("Service.java", textwrap.dedent("""
    package com.example;
    import java.util.*;
    @Service
    public class MyService {
        public void execute() { System.out.println("Hello"); }
    }
    """)),
    ("app.ts", textwrap.dedent("""
    import { Component } from '@angular/core';
    @Component({})
    export class AppComponent {
        title = 'my-app';
        ngOnInit() { console.log('Init'); }
    }
    """)),
    ("main.cpp", textwrap.dedent("""
    #include <iostream>
    #include "header.h"
    namespace utils {
        void process() { std.cout << "Processing" << std.endl; }
    }
    class Node {
        public:
            void draw() {}
    };
    """)),
    ("logic.py", textwrap.dedent("""
    import os
    @cache
    def get_data():
        return "data"
    """))
]

for path, code in test_cases:
    print(f"\n--- Testing {path} ---")
    res = get_parser_result(path, code)
    if res.get('error'):
        print(f"Error: {res.get('error')}")
    print(f"Lines: {res.get('line_count')}")
    print(f"Keywords: {res.get('keywords')}")
    if res.get('imports'): print(f"Imports: {res.get('imports')}")
    if res.get('classes'): print(f"Classes: {res.get('classes')}")
    if res.get('functions'): print(f"Functions: {res.get('functions')}")
