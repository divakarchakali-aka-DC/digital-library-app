-- Switch to the database
USE digital_library;

-- Users table (for auth)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(120) NOT NULL,
    role VARCHAR(20) DEFAULT 'user'
);

-- Books table (simplified - without description and category)
CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(100) NOT NULL,
    author_bio TEXT,
    image_url VARCHAR(500),
    book_url VARCHAR(500) NOT NULL,
    available BOOLEAN DEFAULT TRUE
);

-- Borrows table
CREATE TABLE IF NOT EXISTS borrows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_id INT NOT NULL,
    borrow_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    return_date DATETIME NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (book_id) REFERENCES books(id)
);

-- Insert DevOps-Related Free Books with OFFICIAL documentation links only
INSERT IGNORE INTO books (title, author, author_bio, image_url, book_url, available) VALUES 

-- 1. The Linux Command Line (Official free ebook)
('The Linux Command Line', 'William Shotts', 'William Shotts is a retired U.S. Navy submarine officer and command-line enthusiast who has been working with Linux since 1998. He is the author of this comprehensive guide to mastering the Linux shell for everyday tasks.', 
 'https://linuxcommand.org/images/lcl2_front_new.png',
 'https://linuxcommand.org/tlcl.php', 
 TRUE),

-- 2. Pro Git (2nd Edition) (Official free ebook)
('Pro Git (2nd Edition)', 'Scott Chacon, Ben Straub', 'Scott Chacon is a Git consultant and co-founder of GitHub; Ben Straub is a software engineer specializing in Git tooling and documentation. Together, they provide the definitive guide to Git.', 
 'https://git-scm.com/images/progit2.png',
 'https://git-scm.com/book/en/v2', 
 TRUE),

-- 3. Docker Documentation (Official)
('Docker Documentation', 'Docker, Inc.', 'Docker, Inc. develops the Docker platform and maintains comprehensive documentation for containerization technology used by millions of developers worldwide.', 
 'https://www.docker.com/app/uploads/2022/03/vertical-logo-monochromatic.png',
 'https://docs.docker.com/get-started/overview/', 
 TRUE),

-- 4. Kubernetes Official Documentation
('Kubernetes Documentation', 'The Kubernetes Authors', 'Kubernetes is an open-source container orchestration system originally designed by Google and now maintained by the Cloud Native Computing Foundation.', 
 'https://www.svgrepo.com/show/376331/kubernetes.svg',
 'https://kubernetes.io/docs/tutorials/', 
 TRUE),

-- 5. Terraform Official Documentation
('Terraform by HashiCorp', 'HashiCorp', 'HashiCorp is the company behind Terraform, providing infrastructure as code tools for provisioning and managing cloud resources across multiple providers.', 
 'https://www.svgrepo.com/show/354444/terraform.svg',
 'https://developer.hashicorp.com/terraform/docs', 
 TRUE),

-- 6. Ansible Documentation
('Ansible Documentation', 'Red Hat', 'Ansible is an open-source automation tool acquired by Red Hat, used for configuration management, application deployment, and IT orchestration.', 
 'https://www.svgrepo.com/show/353399/ansible.svg',
 'https://docs.ansible.com/ansible/latest/index.html', 
 TRUE),

-- 7. Prometheus Documentation
('Prometheus Documentation', 'Prometheus Authors', 'Prometheus is an open-source systems monitoring and alerting toolkit originally built at SoundCloud and now part of the Cloud Native Computing Foundation.', 
 'https://www.svgrepo.com/show/354219/prometheus.svg',
 'https://prometheus.io/docs/introduction/overview/', 
 TRUE),

-- 8. Jenkins Documentation
('Jenkins Handbook', 'Jenkins Community', 'Jenkins is an open-source automation server that provides hundreds of plugins to support building, deploying, and automating any project.', 
 'https://www.jenkins.io/images/logo-title-opengraph.png',
 'https://www.jenkins.io/doc/', 
 TRUE),

-- 9. AWS DevOps Guide
('AWS DevOps Guide', 'Amazon Web Services', 'AWS provides comprehensive documentation for implementing DevOps practices using their cloud services and tools.', 
 'https://a0.awsstatic.com/libra-css/images/logos/aws_logo_smile_1200x630.png',
 'https://docs.aws.amazon.com/whitepapers/latest/introduction-devops-aws/introduction-devops-aws.html', 
 TRUE),

-- 10. Google Cloud DevOps
('Google Cloud DevOps Documentation', 'Google Cloud', 'Google Cloud Platform provides extensive documentation for DevOps practices including CI/CD, monitoring, and infrastructure management.', 
 'https://cloud.google.com/_static/cloud/images/social-icon-google-cloud-1200-630.png',
 'https://www.cloudskillsboost.google/paths/20', 
 TRUE),

-- 11. Azure DevOps Documentation
('Azure DevOps Documentation', 'Microsoft', 'Microsoft Azure provides comprehensive DevOps documentation for implementing CI/CD, infrastructure as code, and monitoring solutions.', 
 'https://azurecomcdn.azureedge.net/cvt-663a30b49b10b13c3d83c4da48e138a62a673fafe8f3b7e7c7ae47506b15e8f3/images/shared/social/azure-icon-250x250.png',
 'https://learn.microsoft.com/en-us/azure/devops/?view=azure-devops', 
 TRUE),

-- 12. GitLab CI/CD Docs
('GitLab CI/CD Documentation', 'GitLab', 'GitLab provides comprehensive documentation for their complete DevOps platform including source code management, CI/CD, and monitoring.', 
 'https://about.gitlab.com/images/press/logo/svg/gitlab-logo-gray-rgb.svg',
 'https://docs.gitlab.com/ee/ci/', 
 TRUE),

-- 13. GitHub Actions Docs
('GitHub Actions Documentation', 'GitHub', 'GitHub Actions enables automation of workflows directly in your GitHub repository for CI/CD and DevOps practices.', 
 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png',
 'https://docs.github.com/en/actions', 
 TRUE),

-- 14. NGINX Documentation
('NGINX Documentation', 'F5 Networks', 'NGINX is a high-performance web server, reverse proxy, and load balancer used extensively in modern DevOps environments.', 
 'https://www.nginx.com/wp-content/uploads/2020/05/NGINX-product-icon.svg',
 'https://nginx.org/en/docs/', 
 TRUE);

-- Insert classic literature from Project Gutenberg (official free ebooks)
INSERT IGNORE INTO books (title, author, author_bio, image_url, book_url, available) VALUES 
('1984', 'George Orwell', 'George Orwell (1903-1950) was an English novelist, essayist, and critic known for his dystopian novel 1984, which explores themes of surveillance and totalitarianism.', 
 'https://www.gutenberg.org/cache/epub/60/pg60.cover.medium.jpg',
 'https://www.gutenberg.org/ebooks/60',
 TRUE),

('Pride and Prejudice', 'Jane Austen', 'Jane Austen (1775-1817) was an English novelist known for her six major novels which interpret and critique the British landed gentry.', 
 'https://www.gutenberg.org/cache/epub/1342/pg1342.cover.medium.jpg',
 'https://www.gutenberg.org/ebooks/1342',
 TRUE),

('The Adventures of Sherlock Holmes', 'Arthur Conan Doyle', 'Arthur Conan Doyle (1859-1930) was a British writer and physician, best known for creating the detective Sherlock Holmes.', 
 'https://www.gutenberg.org/cache/epub/1661/pg1661.cover.medium.jpg',
 'https://www.gutenberg.org/ebooks/1661',
 TRUE);