// Asset-free host. Identity constants are generated from PROJECT_CONTEXT.md.
#include "runtime.h"
#include "identity.h"
#include <windows.h>
#include <bcrypt.h>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

static std::string sha256(const std::vector<unsigned char>& bytes) {
    BCRYPT_ALG_HANDLE algorithm = nullptr;
    BCRYPT_HASH_HANDLE hash = nullptr;
    unsigned char digest[32];
    bool ok = BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) >= 0;
    if (ok) ok = BCryptCreateHash(algorithm, &hash, nullptr, 0, nullptr, 0, 0) >= 0;
    if (ok) ok = BCryptHashData(hash, const_cast<unsigned char*>(bytes.data()),
                              static_cast<ULONG>(bytes.size()), 0) >= 0;
    if (ok) ok = BCryptFinishHash(hash, digest, sizeof(digest), 0) >= 0;
    if (hash) BCryptDestroyHash(hash);
    if (algorithm) BCryptCloseAlgorithmProvider(algorithm, 0);
    if (!ok) return {};
    const char* digits = "0123456789abcdef";
    std::string result;
    for (unsigned char value : digest) {
        result += digits[value >> 4];
        result += digits[value & 15];
    }
    return result;
}

int main(int argc, char** argv) {
    const char* rom = nullptr;
    const char* bios = nullptr;
    for (int index = 1; index < argc; ++index) {
        const std::string arg = argv[index];
        if (arg == "--rom" && index + 1 < argc) rom = argv[++index];
        if (arg == "--bios" && index + 1 < argc) bios = argv[++index];
        if (arg == "--rom-sha1" || arg == "--rom-crc32") {
            std::fprintf(stderr, "This build accepts only its verified cartridge revision.\n");
            return 2;
        }
    }
    if (!rom || !bios) {
        std::fprintf(stderr, "Usage: RoadRashJailbreakRecomp --rom <your ROM.gba> --bios <local BIOS.bin> [--frames N] [--window]\n");
        return 2;
    }
    std::ifstream input(rom, std::ios::binary);
    const std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(input)), {});
    if (bytes.size() != RRJ_ROM_SIZE || sha256(bytes) != RRJ_ROM_SHA256) {
        std::fprintf(stderr, "ROM size or SHA256 differs from this build's baseline.\n");
        return 1;
    }
    std::ifstream bios_input(bios, std::ios::binary);
    const std::vector<unsigned char> bios_bytes((std::istreambuf_iterator<char>(bios_input)), {});
    if (bios_bytes.size() != 16384 || sha256(bios_bytes) != RRJ_BIOS_SHA256) {
        std::fprintf(stderr, "BIOS differs from the image translated into this build.\n");
        return 1;
    }
    gbarecomp::RunOptions options;
    options.builtin_game_name = "Road Rash: Jailbreak";
    options.builtin_rom_sha1 = RRJ_ROM_SHA1;
    options.freely_resizable_window = true;
    options.show_fps_by_default = true;
    std::vector<char*> runtime_args(argv, argv + argc);
    runtime_args.push_back(const_cast<char*>("--rom-sha1"));
    runtime_args.push_back(const_cast<char*>(RRJ_ROM_SHA1));
    runtime_args.push_back(const_cast<char*>("--bios-sha1"));
    runtime_args.push_back(const_cast<char*>(RRJ_BIOS_SHA1));
    return gbarecomp::run_game(static_cast<int>(runtime_args.size()), runtime_args.data(), options);
}
