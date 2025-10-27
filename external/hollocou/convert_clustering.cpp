#include <iostream>
#include <fstream>
#include <unordered_map>
#include <sstream>
#include <string>

using namespace std;

int main(int argc, char **argv)
{
    unordered_map<int, int> clusters;

    ifstream inFile;
    inFile.open(argv[1]);

    int c = 0;
    string line;
    int N = 0;
    while (getline(inFile, line))
    {
        istringstream iss(line);
        int u;
        int n = 0;
        while (iss >> u)
        {
            N = max(N, u + 1);
            clusters[u] = c;
            n++;
        }

        c++;

        if (n == 0)
            break;
    }

    inFile.close();

    ofstream outFile;
    outFile.open(argv[2]);

    for (int u = 0; u < N; u++)
    {
        outFile << clusters[u] << endl;
    }

    outFile.close();

    return 0;
}