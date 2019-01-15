class Locators:

    # Directory page related locators
    side_nav_directory = "//div[@id='sidenav-list']//ul/li/a[@href='/directory/']"
    search_text_box = "//input[@type='text']"
    actual_search_text = "//div[@class='list-body']/a"
    no_result = "//div[contains(text(),'No Results')]"
    total_org_list = "//div[@class='list-body']/a"
    actual_organization = "//a[@href = '/directory/#total']//span[@class='number _700']"

    # Help and FAQ page related locators
    side_nav_help_and_faq = "//a[@href = '/faq/']/span[contains(text(),'Help & FAQ')]"
    actual_total_questions = "//div[@class='box-header']/a"
    actual_total_answers = "//div[@class='box-body px-4']//p"
