void main(){
  int i, j=2;
  int *r;
  int y[5] = {1,2,3,4,5};
  r = &y[j];
  i = y[j];
  y[i] = i + j;
  return;
}
