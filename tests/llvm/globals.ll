; ModuleID = 'tests\llvm\globals.c'
source_filename = "tests\\llvm\\globals.c"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-windows-msvc19.11.0"

@i = dso_local global i32 1, align 4
@f = dso_local global float 0x3FB99999A0000000, align 4
@c = dso_local global i8 99, align 1
@vi = dso_local global [3 x i32] [i32 1, i32 2, i32 3], align 4
@vf = dso_local global [3 x float] [float 0x3FB99999A0000000, float 0x3FC99999A0000000, float 0x3FD3333340000000], align 4
@vc = dso_local global [4 x i8] c"hey\00", align 1

; Function Attrs: noinline nounwind optnone uwtable
define dso_local void @main() #0 {
  ret void
}

; Function Attrs: noinline nounwind optnone uwtable
define dso_local void @test() #0 {
  ret void
}

attributes #0 = { noinline nounwind optnone uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "frame-pointer"="none" "less-precise-fpmad"="false" "min-legal-vector-width"="0" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.module.flags = !{!0, !1}
!llvm.ident = !{!2}

!0 = !{i32 1, !"wchar_size", i32 2}
!1 = !{i32 7, !"PIC Level", i32 2}
!2 = !{!"clang version 10.0.0 "}
