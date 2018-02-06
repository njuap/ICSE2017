'''
author: Wanwangying Ma
date: Mar. 7th, 2016

username: GitHub login
password: GitHub password

input: url.csv
       the link of a GitHub repository and the label name indicating bug issues
        
output:
1. subjectProjectName_basic.csv
   the basic information of all bugs in subjectProject, collected by using GitHub API
2. subjectProjectName_participants&close.csv 
   all the developers participating the discussion of each bug in subjectProject and
   the information about closing every bug(closer, closed time, and patch), 
   collected by parsing the issue report pages  
3. subjectProjectName_related.csv
   all the related issues with every bugs in subjectProject, by identifying the explicit
   link in comments
4. subjectProjectName_refs.csv
   all the related issues with every bugs in subjectProject, by identifying the automatic
   hint in issue report pages.
5. subjectProjectName_related_basic.csv
   the basic information of all the related issues with all bugs in subjectProject, collected
   by using GitHub API.
6. subjectProjectName_related_summary.csv
   other information of all the related issues with all bugs in subjectProject, collected
   by parsing the issue report pages

'''

import requests
import bs4
import re
import csv
from collections import namedtuple
from pygithub3 import Github

username = 'username'
password = 'password'
gh = Github(username, password)

def get_basic(issue):
    
#    print("============", issue.id, "===============")

    issue_id = issue.id
    created_at = str(issue.created_at)
    updated_at = str(issue.updated_at)
    closed_at = str(issue.closed_at)
    state = issue.state
    assignee = issue.assignee
    if(assignee):
        assignee = assignee.login     
    comments = issue.comments
    title = issue.title
    if(title):
        title = title.encode("GBK", 'ignore')
    url = issue.url
    body = issue.body
    if(body):
        body = body.encode("GBK", 'ignore')
    reporter = issue.user.login
    if issue.closed_by:
        closed_by = issue.closed_by.login
    else:
        closed_by = None
                            
    labels = issue.labels
    label_names = []
    for label in labels:
        label_names.append(label.name)
    sep =';'
    label_name = sep.join(label_names)                
           
    milestone = issue.milestone
    if milestone is not None:
        milestone = milestone.title

                
    issue = {'id':issue_id, 'reporter':reporter, 'closed_by':closed_by, 'created_at':created_at, 
            'updated_at':updated_at, 'closed_at':closed_at, 'state':state, 'assignee':assignee, 
            'milestone':milestone, 'comments':comments, 'label_name':label_name, 'title':title, 
            'url':url, 'body':body}

    return (issue)
                
                
def get_html(url):
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    return (soup)

def get_related(content,user,projectName):
    '''
    possible format:
        #6776  $$this lead to some false positive
        njues/project1#1
        https://github.com/numpy/numpy/issues/1683    https://github.com/numpy/numpy/issues/5241#issuecomment-125405573
        https://github.com/scipy/scipy/pull/58
        gh-1683
    return issues:
        [repo_name#6776, njues/project1#1, numpy/numpy#1683, repo_name#1683]
    '''
#    print("get related issues......")
    repo_name = user + '/' + projectName
    issues = []
    formats = ['\W(#[1-9]+[0-9]*)',
               '(\w+\/\w+#[1-9]+[0-9]*)',
               'github.com\/(\w+\/\w+)\/(issues|pull)\/([1-9]+[0-9]*)',
               'gh-([1-9]+[0-9]*)']
    
    for i in range(len(formats)):
        pattern = re.compile(formats[i])
        match = pattern.findall(str(content))
        for m in match:
            if i==0:
                issues += ([repo_name + m])
            elif i==1:
                issues += ([m])
            elif i==2:
                issues += ([m[0] + '#' + m[2]])
            elif i==3:
                issues += ([repo_name + '#' + m])
#    print(issues)
    
    cross_issues = []
    within_issues = []   
#    print (repo_name)    
    issues = set(issues)    
    for issue in issues:
#        print (issue)
        if repo_name not in issue:
            cross_issues.append(issue)
        else:
            within_issues.append(issue)
    
    return (within_issues, cross_issues)

def get_ifRelated(content,projectName,subId):
    if (subId in str(content)) and (projectName in str(content)):
        return True
    else:
        return False  

def get_comments(issue):
    times = []
    authors = []
    comments = []
    
    contents = issue.get_comments()
    for content in contents:
        times.append(str(content.created_at))
        authors.append(content.user.login)
        comments.append(content.body)
        
    return (times, authors, comments, len(comments))


def get_participants(soup):
    participants = soup.select('div[id="partial-users-participants"] div[class^="discussion-sidebar-heading"]')
    npart = re.findall(r'(\w*[0-9]+)\w*',participants[0].get_text())[0]
    names = []
    parts = soup.select('div[class="participation-avatars"] a[class$="tooltipped-n"]')
    for part in parts:
        names.append(part['aria-label'])
    return (npart, names)    

def get_close(soup, itype):  
    
    author = None
    issue = None
    time = None
    ctype = None
    
    if itype is 'pr':
        merge = soup.select(".discussion-item.discussion-item-merged.js-details-container")
        if merge:
            res = merge[0].select('a')
            if len(res)==3:
                author = res[0].get_text()
                issue = res[1].get_text()
                time = res[2].contents[0]['datetime']
                ctype = 'merge'
                return (author, issue, time, ctype)
            if len(res)==2:
                author = res[0].get_text()
                issue = merge[0].select('code[class="text-emphasized"]')[0].get_text()
                time = res[1].contents[0]['datetime']
                ctype = 'merge'
                return (author, issue, time, ctype)
        
    if itype is'issue':
#        print ('this is an issue.')
        close = soup.select('div[class$="discussion-item-closed"]')
        if close:
            res = close[len(close)-1].select('a')
            if len(res)==3:
                author = res[0].get_text()
                issue = res[1].get_text()
                time = res[2].contents[0]['datetime']
                ctype = 'close'
                return (author, issue, time, ctype)
            if len(res)==2:
                author = res[0].get_text()
                issue = ''
                time = res[1].contents[0]['datetime']
                ctype = 'close'
                return (author, issue, time, ctype)
        
    return (author, issue, time, ctype)
        
def get_pr(soup, projectName, itype):
    print ("get pr......")
    refs = soup.select('div[class$="discussion-item-ref"]')
    res =[]
    for ref in refs:
        if ((itype == "issue") and (ref.select('div[id^="ref-pullrequest"]'))) or ((itype == "pr") and (ref.select('div[id^="ref-issue"]'))):
            prs = ref.select('h4[class="discussion-item-ref-title"] a[class="title-link"]')
            for pr in prs:
                if projectName in pr['href']:                
                    res.append(re.sub(r'[\n\s]', '',pr.span.get_text()))
    return (res)

def get_refs(soup, projectName):

#    res = soup.select('span[class="issue-num"]') 
    res = soup.select('h4[class="discussion-item-ref-title"] a[class="title-link"]')
    
    cross_refs=[]
    within_refs=[]
    for r in res:
        if projectName in r['href']:
            within_refs.append(r['href'])
        else:
            cross_refs.append(r['href'])
         
    commits = soup.select('td[class="commit-meta"] a[class="commit-id]')
    crefs = []
    for c in commits:
        crefs.append(c['href'])
    
    return (within_refs, cross_refs, crefs)

    
def get_subjectIssueInfo(subjectUser, subjectProjectName, issue_number, root_url, issue):   
    index_url = root_url + str(issue_number)
    related_issues = set()
    try:
        soup = get_html(index_url)
        title = soup.title.get_text()
        if "Pull Request" in title:
            itype = "pr"
        else:
            itype = "issue"
#        print (itype)
            
        print ("get basic information......")    
        sb = get_basic(issue)
        sb.update({'issue':issue_number})
        
        print ("get related......")                
        ctimes, cauthors, comments, ncomments = get_comments(issue)
        ctimes.insert(0, sb['created_at'])
        cauthors.insert(0, sb['reporter'])
        comments.insert(0, sb['body'])
        ncomments  = ncomments + 1
    
#        print(range(len(ctimes)))
        sr_result=[]
        for j in range(len(comments)):
            within_releted, cross_related = get_related(comments[j],subjectUser,subjectProjectName)
            print('cross related: ' , len(cross_related))
            print('within related: ' , len(within_releted))
            if (len(cross_related)>0):
                print("cross_issues:")
                for cr in cross_related:
                    sr_result.append({'number':issue_number, 'issue_rel':cr, 'rel_time':ctimes[j], 'rel_author':cauthors[j], 'rel_comment':j, 
                                'type':'cross'})
                    related_issues.add(cr)
                    print(cr)

            if (len(within_releted)>0):
                print("within_issues:")
                for wr in within_releted:
                    print (wr)
                    sr_result.append({'number':issue_number, 'issue_rel':wr, 'rel_time':ctimes[j], 'rel_author':cauthors[j], 'rel_comment':j, 
                                'type':'within'})
        
        print ("get refs......")
        within_refs, cross_refs, commit_refs = get_refs(soup, subjectProjectName)
        ref_result = {'number':issue_number, 'within_refs':within_refs, 'cross_refs':cross_refs, 'commit_refs':commit_refs}
        for cr in cross_refs:
            cr = cr.replace('/issues/','#')[1:]
            print('************', cr)
            related_issues.add(cr)       
             
        print ("get close related......") 
        author, close, time, ctype = get_close(soup, itype)
        print (author)
        pr = []
        pr = get_pr(soup, subjectProjectName, itype)
        
        print("get participants......")
        npart, pnames = get_participants(soup)
        sp_result = {'number':issue_number, 'itype':itype, 'close_author':author, 'close_time':time, 
                    'close':close, 'close_type':ctype, 'related_pr':pr, '#comment':ncomments,
                    '#participants':npart, 'part_names':pnames} 
        
    except Exception as e:
        print(subjectProjectName, '#', issue_number, ': ', e)  
        with open (subjectProjectName+'_err_log.txt', 'a') as ef:
            ef.write(subjectProjectName + '#' +str(issue_number) + ': ' + str(e) + '\t\n') 
                                
    return (sb, sr_result, sp_result, ref_result, related_issues)
                       
def get_refIssueInfo(subjectProjectName, refIssue, subIssue):
    temp = re.split(r'[/#]',refIssue)
    user = temp[0]
    projectName = temp[1]
    ref_id = temp[2]
    ref_index_url = 'https://github.com/' + user + '/' + projectName + '/issues/' + ref_id
            
    b_result = {}
    r_result = {}
    
    try:
        soup = get_html(ref_index_url)
        title = soup.title.get_text()
        if "Pull Request" in title:
            itype = "pr"
        else:
            itype = "issue"
        
        repo = gh.get_repo(user+'/'+ projectName)
        issue = repo.get_issue(int(ref_id.strip()))
        
        print ("get basic information......")    
        b_result = get_basic(issue)
        name = {'issue':refIssue}
        b_result.update(name)
        
        print ("get close related......") 
        author, close, time, ctype = get_close(soup, itype)
        pr = []
        pr = get_pr(soup, projectName, itype)
        r_result = {'ref_issue':refIssue, 'number':subIssue, 'itype':itype, 'close_author':author, 'close_time':time, 
                    'close':close, 'close_type':ctype, 'related_pr':pr}    
                
        print("get participants......")
        npart, pnames = get_participants(soup)
        p_result = {'#participants':npart, 'part_names':pnames}                    
                   
        print ("get related......")                
        ctimes, cauthors, comments, ncomments = get_comments(issue)
        ctimes.insert(0, b_result['created_at'])
        cauthors.insert(0, b_result['reporter'])
        comments.insert(0, b_result['body'])
        ncomments  = ncomments + 1
        
        ref_result={'#comment':ncomments}
        for j in range(len(comments)):
            if (get_ifRelated(comments[j],subjectProjectName, str(subIssue))):
                ref_result.update({'ref_time':ctimes[j], 'ref_author':cauthors[j], 'ref_comment':j})
#                print (ref_result)
                break
                
        r_result.update(p_result)
        r_result.update(ref_result)
                                   

                
    except Exception as e:
        print(subIssue, '-->', refIssue, ': ', e)  
        with open (subjectProjectName+'_related_err_log.txt', 'a') as ef:
            ef.write(str(subIssue) + '-->' + str(refIssue) + ': ' + str(e) + '\t\n')   
            
    return (b_result, r_result)
     
def get_all(subjectUser, subjectProjectName, labelName):
    
    b_headers = ['issue', 'id', 'reporter', 'closed_by', 'created_at', 'updated_at', 'closed_at', 'state', 
                 'assignee', 'milestone', 'comments', 'label_name', 'url', 'title', 'body']
    
    #==================for subject project===========================================
    sr_headers = ['number', 'issue_rel', 'rel_time', 'rel_author', 'rel_comment', 'type']
    sr = open(subjectProjectName + '_related.csv','w',newline='')  
    sr_csv = csv.DictWriter(sr, sr_headers)
    sr_csv.writeheader()
   
    sp_headers = ['number', 'itype', 'close_author', 'close_time', 'close', 'close_type', 
                  'related_pr', '#comment', '#participants','part_names']    
    sp = open(subjectProjectName + '_participants&close.csv','w',newline='')
    sp_csv = csv.DictWriter(sp, sp_headers)
    sp_csv.writeheader()
   
    sref_headers = ['number', 'within_refs', 'cross_refs', 'commit_refs']
    sref = open(subjectProjectName + '_refs.csv','w',newline='')
    sref_csv = csv.DictWriter(sref, sref_headers)
    sref_csv.writeheader()
    
    sb = open(subjectProjectName + '_basic.csv','w',newline='')
    sb_csv = csv.DictWriter(sb, b_headers)
    sb_csv.writeheader()
    
    #==================for related issues================================================
    r_headers = ['ref_issue', 'number', 'ref_time', 'ref_author', 'ref_comment', 'itype', 
                 'close_author', 'close_time', 'close', 'close_type', 'related_pr',
                 '#comment', '#participants','part_names']
    r = open(subjectProjectName + '_related_summary.csv','w',newline='')
    r_csv = csv.DictWriter(r,r_headers)
    r_csv.writeheader()
    
    rb = open(subjectProjectName + '_related_basic.csv','w',newline='')
    rb_csv = csv.DictWriter(rb, b_headers)
    rb_csv.writeheader()
        
    

    #===================get bugs of subject project===========================================================
    
    repo = gh.get_repo(subjectUser+'/'+subjectProjectName)
    
    if labelName == 'No':
        print('yes!')
        issues = issues = repo.get_issues(state='closed')
    else:
        label =[]
        label.append(repo.get_label(labelName))
        issues = repo.get_issues(state='closed', labels=label)
#    print ("number of closed bugs: ", issues.totalCount())
    root_url = 'https://github.com/' + subjectUser + '/' + subjectProjectName + '/issues/'
    
    issue_count = 0
    ri_count = 0
    for issue in issues:
        print ('issue: ', issue.number)
        sb_result, sr_result, sp_result, ref_result, related_issues = get_subjectIssueInfo(subjectUser, subjectProjectName, issue.number, root_url, issue)
        sb_csv.writerow(sb_result) 
        for item in sr_result:
            sr_csv.writerow(item)
        sp_csv.writerow(sp_result)
        sref_csv.writerow(ref_result)
        sb.flush()
        sr.flush()
        sp.flush()
        sref.flush()
        issue_count = issue_count +1
               
        for ri in related_issues:
            print (issue.number, '-->', ri)
            rb_result, r_result = get_refIssueInfo(subjectProjectName, ri, issue.number)
            rb_csv.writerow(rb_result)
            r_csv.writerow(r_result)
            rb.flush()
            r.flush()
            ri_count = ri_count + 1
            
    sb.close()
    sr.close()
    sp.close()
    sref.close()
    rb.close()
    r.close()
    
    return (issue_count, ri_count)

def getProjectIssueWithRelated(urlFile):
    s = open('/summary.csv','a' ,newline='')
    s_headers = ['project', 'organization', 'url', 'label_name','closed','bugs']
    s_csv = csv.DictWriter(s,s_headers)
    s_csv.writeheader()
    
    with open(urlFile) as f:
        f_csv = csv.reader(f)
        headings = next(f_csv)
        Row = namedtuple('Row', headings)
        for r in f_csv:
            row = Row(*r)
            url = row.url
            temp = re.split('/',url)
            user = temp[-2]
            projectName = temp[-1]
            labelName = row.bug_label
            
            print('user:', user)
            print('project:', projectName)
            print('bug label:', labelName)
            print('type:', len(labelName))
            issue_count, ri_count = get_all(user, projectName, labelName)
            result = {'project':projectName, 'organization':user, 'url':url, 'label_name':labelName,
                      'closed':issue_count, 'bugs':ri_count}
            s_csv.writerow(result)
            s.flush()
    
    s.close()
            


getProjectIssueWithRelated('/url.csv')
            
            
             
 
        
