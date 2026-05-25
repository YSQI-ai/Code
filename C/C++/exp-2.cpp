#include <bits/stdc++.h>
using namespace std;
const int MAXN = 1005;
int a[15];
int main()
{
    int num;
    while (cin >> num)
    {
        if (num >= 1 && num <= 10)
        {
            a[num]++;
        }
    }
    for (int i = 1; i <= 10; ++i)
    {
        cout << "第" << i << "号歌手的选票数为：" << a[i] << endl;
    }
    return 0;
}