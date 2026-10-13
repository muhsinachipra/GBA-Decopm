cmake_minimum_required(VERSION 3.20)
project(RoadRashJailbreakRecomp LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT EXISTS "${RRJ_FRAMEWORK}/CMakeLists.txt" OR
   NOT EXISTS "${RRJ_GENERATED}/identity.h")
    message(FATAL_ERROR "Run python tools/recomp/build.py first")
endif()
add_subdirectory("${RRJ_FRAMEWORK}" framework)
file(GLOB RRJ_SHARDS CONFIGURE_DEPENDS "${RRJ_GENERATED}/recompiled_*.cpp")
add_executable(RoadRashJailbreakRecomp main.cpp ${RRJ_SHARDS}
    "${RRJ_GENERATED}/dispatch_table.cpp"
    "${RRJ_GENERATED}/symbol_map.cpp")
target_include_directories(RoadRashJailbreakRecomp PRIVATE "${RRJ_GENERATED}")
target_link_gbarecomp_runtime_stack(RoadRashJailbreakRecomp)
target_link_libraries(RoadRashJailbreakRecomp PRIVATE bcrypt)
gbarecomp_stage_mingw_runtime(RoadRashJailbreakRecomp)
