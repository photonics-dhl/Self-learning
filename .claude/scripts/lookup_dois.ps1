$dois = @(
    # Quantum optics fundamentals
    '10.1103/RevModPhys.77.513',
    '10.1103/RevModPhys.71.518',
    '10.1103/RevModPhys.82.1155',
    '10.1103/RevModPhys.85.553',
    '10.1103/RevModPhys.75.457',
    '10.1103/RevModPhys.74.145',
    '10.1103/RevModPhys.70.1009',
    '10.1103/RevModPhys.75.107',
    '10.1103/RevModPhys.82.2313',
    '10.1103/RevModPhys.86.187',
    '10.1103/RevModPhys.83.33',
    '10.1103/RevModPhys.84.77',
    '10.1103/RevModPhys.84.623',
    '10.1103/RevModPhys.73.319',
    '10.1103/RevModPhys.80.541',
    '10.1103/RevModPhys.90.035005',
    '10.1103/RevModPhys.89.035002',
    '10.1103/RevModPhys.88.021002',
    '10.1103/RevModPhys.81.299',
    '10.1103/RevModPhys.78.1137',
    '10.1103/RevModPhys.85.1083',
    '10.1103/RevModPhys.92.025002',
    '10.1103/RevModPhys.93.025001',
    '10.1103/RevModPhys.95.035001',
    '10.1103/RevModPhys.94.015001',
    # Advances in Optics and Photonics
    '10.1364/AOP.3.000306',
    '10.1364/AOP.5.000271',
    '10.1364/AOP.6.000337',
    '10.1364/AOP.7.000456',
    '10.1364/AOP.2.000395',
    '10.1364/AOP.9.000356',
    # Nature Photonics / Nature Physics
    '10.1038/nphoton.2009.251',
    '10.1038/nphoton.2012.326',
    '10.1038/nphoton.2007.223',
    '10.1038/nphys1286',
    '10.1038/nphys2355',
    '10.1038/nphoton.2013.271',
    '10.1038/s41566-018-0320-2',
    '10.1038/s41566-019-0552-6',
    # Nature Reviews Physics
    '10.1038/s42254-019-0084-3',
    '10.1038/s42254-020-0177-6',
    # Reports on Progress in Physics
    '10.1088/0034-4885/66/9/201',
    '10.1088/0034-4885/80/1/016001',
    '10.1088/0034-4885/82/1/012001',
    '10.1088/1361-6633/aa9119',
    '10.1088/1361-6633/ab0123',
    '10.1088/0034-4885/74/7/074401',
    # Textbooks
    '10.1017/CBO9780511813993',
    '10.1007/978-3-540-73526-1',
    '10.1093/acprof:oso/9780198506730.001.0001'
)

foreach ($doi in $dois) {
    try {
        $url = "https://api.semanticscholar.org/graph/v1/paper/DOI:$doi?fields=title,authors,year,citationCount,journal,externalIds"
        $r = Invoke-RestMethod -Uri $url -Method Get
        $authorNames = ($r.authors | Select-Object -First 5 | ForEach-Object { $_.name }) -join ', '
        if ($r.authors.Count -gt 5) { $authorNames += ' et al.' }
        $jInfo = ""
        if ($r.journal) {
            $jInfo = "$($r.journal.name) v$($r.journal.volume) pp$($r.journal.pages)"
        }
        Write-Output "DOI:$doi|$($r.title)|$authorNames|$($r.year)|$jInfo|$($r.citationCount)"
        Start-Sleep -Seconds 2
    } catch {
        Write-Output "DOI:$doi|NOT_FOUND||||"
        Start-Sleep -Seconds 1
    }
}
