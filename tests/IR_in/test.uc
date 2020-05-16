int b = 0;

int testA(){
    return 1;
}

void testB(){
    
}

char testC(){
    b = 3;
    return 'c';
}

void main () {
    int x = 0;

    if (b==0) {
        x = 1;
    } else {
        x = 2;
    }

    b = testA();

    for (x=0; x<10; ++x) {
        x++;
    }

    while (x > 0) {
        ++x;
        break;
    }

    assert 1==1;

    return;
}