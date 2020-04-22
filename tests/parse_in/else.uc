int main (){
    int a = 1;
    
    if (a == 1) {
        print("if 1");
    }

    if (a == 0){
        print("if 2");
        if (a == 1) {
            print("if Nested");
        }
    } else {
        print("else");
    }

}
