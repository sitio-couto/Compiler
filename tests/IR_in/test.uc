int b = 0;

int test(){
    return 1;
}

void main () {
    int x = 0;

    if (b==0) {
        x = 1;
    } else {
        x = 2;
    }

    b = test();

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