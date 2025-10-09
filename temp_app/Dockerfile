# --- Build stage ---
# Use latest Flutter SDK (Dart >= 3.6 to satisfy your pubspec deps)
FROM ghcr.io/cirruslabs/flutter:latest AS build

WORKDIR /app

# Copy only pubspec files first (better caching of dependencies)
COPY pubspec.* ./

# Get dependencies
RUN flutter pub get

# Copy the rest of the project
COPY . .

# Build the release APK (change to "flutter build web" if targeting web)
RUN flutter build apk --release

# --- Release stage ---
FROM busybox:glibc AS release

WORKDIR /app
COPY --from=build /app/build/app/outputs/flutter-apk/app-release.apk ./app-release.apk

CMD ["echo", "✅ Flutter build complete! APK is available inside the container at /app/app-release.apk"]
