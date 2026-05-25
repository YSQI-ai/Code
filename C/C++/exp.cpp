#include <bits/stdc++.h>
#include <iostream>
#include <map>
using namespace std;
const int MAXN = 10010;
int a[100], N;
int main()
{
    cin >> N;
    for (int i = 0; i < N; i++)
        cin >> a[i];
    int *p = &a[N - 1];
    for (int i = 0; i < N; i++)
    {
        cout << *p << " ";
        p--;
    }
    return 0;
}