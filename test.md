# Collobo Station

## One-line Introduction
A collaboration application for university students and team projects, supporting user authentication and data management via Firebase.

## Problem Being Solved
Provides a platform that enables university students and team project users to easily collaborate and share information with teammates. This application helps users manage information and communicate efficiently through memo management and dynamic list display features.

## Key Features
- **User Authentication**: Secure login functionality via Firebase Authentication.
- **Memo Management**: Functionality for users to create and manage memos.
- **Dynamic List Display**: Provides users with real-time updated lists using RecyclerView.
- **Modern UI**: Implements an intuitive and modern user interface using Jetpack Compose and Material Design.

## Tech Stack
![Kotlin](https://img.shields.io/badge/Kotlin-7F52B5?style=flat&logo=kotlin&logoColor=white)
![Android](https://img.shields.io/badge/Android-3DDC84?style=flat&logo=android&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-FFCA28?style=flat&logo=firebase&logoColor=white)
![Gradle](https://img.shields.io/badge/Gradle-02303A?style=flat&logo=gradle&logoColor=white)

## Folder Structure
```

/
├── app/
│   ├── src/
│   │   ├── androidTest/
│   │   ├── main/
│   │   │   ├── java/
│   │   │   │   └── com/
│   │   │   │       └── example/
│   │   │   │           └── collobo_station/
│   │   │   │               ├── Adapter/
│   │   │   │               ├── Data/
│   │   │   │               ├── Fragment/
│   │   │   │               ├── Login/
│   │   │   │               └── Main/
│   │   │   └── res/
│   │   └── test/
└── build.gradle.kts

```

## Getting Started

### Prerequisites
- Android Studio installed
- Kotlin and Gradle environment configured

### Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/collobo_station.git
   ```

2. Navigate to the project directory:
   ```bash
   cd collobo_station
   ```
3. Install dependencies via Gradle:
   ```bash
   ./gradlew build
   ```
4. Open the project in Android Studio and complete the Firebase configuration.
5. Run the application.

This project is designed to help university students and team project users achieve better outcomes through collaboration. It will continue to evolve through ongoing updates and feedback.
