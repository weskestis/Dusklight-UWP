#define SDL_MAIN_HANDLED
#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>
#include <Windows.h>
#include <winrt/Windows.Storage.h>
#include <winrt/base.h>
#include <array>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>

extern "C" int aurora_main(int argc, char** argv);
namespace fs = std::filesystem;

namespace {
std::string utf8(const fs::path& path) {
    const auto bytes = path.u8string();
    return std::string(bytes.begin(), bytes.end());
}

void envPath(const char* name, const fs::path& value) {
    if (_putenv_s(name, utf8(value).c_str()) != 0) {
        throw std::runtime_error("Cannot set the game path");
    }
}

std::string probeDisc(const fs::path& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) return "Game disc not found.";
    std::array<unsigned char, 32> header{};
    if (!file.read(reinterpret_cast<char*>(header.data()), header.size())) return "The disc file is incomplete.";
    if (header[0x1c] != 0xc2 || header[0x1d] != 0x33 || header[0x1e] != 0x9f || header[0x1f] != 0x3d)
        return "Use an uncompressed GameCube ISO.";
    if (std::string(reinterpret_cast<char*>(header.data()), 6) != "GZLE01" || header[7] != 0)
        return "This preview needs USA Wind Waker, GZLE01 revision 0.";
    return {};
}

bool prelaunch(const fs::path& disc) {
    if (!SDL_Init(SDL_INIT_VIDEO | SDL_INIT_GAMEPAD)) return false;
    SDL_Window* window = SDL_CreateWindow("Zelda Crossover Preview", 1280, 720, 0);
    SDL_Renderer* renderer = window ? SDL_CreateRenderer(window, nullptr) : nullptr;
    if (!renderer) {
        std::fprintf(stderr, "Prelaunch renderer: %s\n", SDL_GetError());
        if (window) SDL_DestroyWindow(window);
        SDL_Quit();
        return false;
    }
    SDL_SetRenderLogicalPresentation(renderer, 640, 360, SDL_LOGICAL_PRESENTATION_LETTERBOX);
    int count = 0;
    SDL_JoystickID* ids = SDL_GetGamepads(&count);
    for (int i = 0; i < count; ++i) SDL_OpenGamepad(ids[i]);
    SDL_free(ids);
    std::string error = probeDisc(disc);
    bool running = true, start = false;
    while (running) {
        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_EVENT_GAMEPAD_ADDED) SDL_OpenGamepad(event.gdevice.which);
            if (event.type == SDL_EVENT_QUIT) running = false;
            const bool keyboard = event.type == SDL_EVENT_KEY_DOWN;
            const bool gamepad = event.type == SDL_EVENT_GAMEPAD_BUTTON_DOWN;
            if ((keyboard && event.key.key == SDLK_ESCAPE) ||
                (gamepad && event.gbutton.button == SDL_GAMEPAD_BUTTON_EAST)) running = false;
            if ((keyboard && event.key.key == SDLK_RETURN) ||
                (gamepad && event.gbutton.button == SDL_GAMEPAD_BUTTON_SOUTH)) {
                error = probeDisc(disc);
                if (error.empty()) { start = true; running = false; }
            }
        }
        SDL_SetRenderDrawColor(renderer, 16, 37, 45, 255);
        SDL_RenderClear(renderer);
        SDL_SetRenderDrawColor(renderer, 233, 205, 138, 255);
        SDL_RenderDebugText(renderer, 36, 48, "ZELDA CROSSOVER");
        SDL_SetRenderDrawColor(renderer, 238, 244, 243, 255);
        SDL_RenderDebugText(renderer, 36, 82, "Wind Waker preview");
        SDL_RenderDebugText(renderer, 36, 126, error.empty() ? "Wind Waker is ready." : error.c_str());
        SDL_RenderDebugText(renderer, 36, 166, "Put your USA GameCube disc image here:");
        SDL_RenderDebugText(renderer, 36, 188, "LocalState/Games/WindWaker/GZLE01.iso");
        SDL_RenderDebugText(renderer, 36, 248, error.empty() ? "A / Enter: Play" : "A / Enter: Check again");
        SDL_RenderDebugText(renderer, 36, 272, "B / Esc: Exit");
        SDL_RenderPresent(renderer);
        SDL_Delay(16);
    }
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    return start;
}

int bootstrap(int argc, char** argv) {
    try {
        const fs::path local(winrt::Windows::Storage::ApplicationData::Current().LocalFolder().Path().c_str());
        const auto user = local / L"WindWaker" / L"user";
        const auto cache = local / L"WindWaker" / L"cache";
        const auto logs = local / L"Logs" / L"WindWaker";
        const auto games = local / L"Games" / L"WindWaker";
        for (const auto& path : {user, cache, logs, games}) fs::create_directories(path);
        FILE* stream = nullptr;
        _wfreopen_s(&stream, (logs / L"boot.log").c_str(), L"wb", stderr);
        setvbuf(stderr, nullptr, _IONBF, 0);
        _wfreopen_s(&stream, (logs / L"stdout.log").c_str(), L"wb", stdout);
        setvbuf(stdout, nullptr, _IONBF, 0);
        std::fprintf(stderr, "Zelda Crossover UWP: Wind Waker startup\n");
        envPath("COS_USER_DIR", user);
        envPath("COS_CACHE_DIR", cache);
        envPath("COS_SETTINGS", user / L"settings.ini");
        envPath("COS_RUN_DIR", logs);
        envPath("COS_DISC", games / L"GZLE01.iso");
        _putenv_s("COS_BACKEND", "d3d12");
        SDL_SetHint(SDL_HINT_JOYSTICK_WGI, "true");
        if (!prelaunch(games / L"GZLE01.iso")) return 0;
        return aurora_main(argc, argv);
    } catch (const winrt::hresult_error& error) {
        OutputDebugStringW(error.message().c_str());
        return 2;
    } catch (const std::exception& error) {
        OutputDebugStringA(error.what());
        return 2;
    }
}
}

int CALLBACK WinMain(HINSTANCE, HINSTANCE, LPSTR, int) {
    return SDL_RunApp(0, nullptr, bootstrap, nullptr);
}
