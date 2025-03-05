from Utilities import Utils
from ProxyStatementHandler import ProxyStatementHandler
import json
import copy
class FileGenerator:
    def __init__(self,input_mode, template_file,model_deployment_name) -> None:
        self.input_mode = input_mode
        self.template_file = template_file
        self.model_deployment_name = model_deployment_name
        self.system_index = 0
        self.user_index = 1
    def generate_batch_file(self,data_parsed):
        batch_file = []
        cik_data = None
        symbol_map = {}
        if self.input_mode == "CSV":
            batch_template = Utils.read_json_data(self.template_file)
            id = 1
            for csv_row in data_parsed:
                symbol = csv_row["Security Symbol"]
                insider = csv_row["Name"]
                custom_id = symbol+"_"+insider
                if custom_id in symbol_map:
                    print("Found duplicate symbol/insider: "+custom_id+", skipping.")
                    continue
                else:
                    symbol_map[custom_id] = True
                proxy_handler = ProxyStatementHandler(csv_row["Security Symbol"])
                if cik_data is None:
                    cik_data = proxy_handler.get_CIK()
                try:
                    proxy_raw = proxy_handler.get_proxy_stmt(symbol,cik_data)
                except:
                    print("Could not get proxy statement for " + symbol)
                    continue
                content = Utils.get_body_from_html(proxy_raw)
                batch_row = copy.deepcopy(batch_template)
                batch_row["custom_id"] = custom_id
                id += 1
                batch_row["body"]["model"] = self.model_deployment_name
                first_last_name = self.split_insider_name(insider)
                question_schema = self.generate_question_schema(insider)
                question_schema_string = json.dumps(question_schema)
                batch_row["body"]["messages"][self.system_index]["role"] = "system"
                batch_row["body"]["messages"][self.system_index]["content"] = "You are a financial analyst, adept at going through complex financial reports and filings to summarize data."\
                        "You are familiar with different forms of compensation including stock, retainers, fees, payments, bonuses, and salaries."\
                        "You have worked with "+first_last_name["full"]+" before and know they may be referred to as "+first_last_name["first"]+" or "+first_last_name["last"]+" in proxy statements."\
                        "You are aware that "+first_last_name["full"]+" is a key executive or director at "+symbol+" and you need to find out more about their compensation, stock ownership, and experience."\
                        "Respond in JSON using the provided schema."
                
                batch_row["body"]["messages"][self.user_index]["role"] = "user"
                batch_row["body"]["messages"][self.user_index]["content"] = "Fill in the provided schema with the information you find in the Proxy Statement. Follow any instructions provided in <brackets> and respond in JSON."\
                "\nOnly focus on information in the Proxy Statement related to "+symbol+". You can ignore information related to other places they've worked. For directors, be careful to look for any retainers mentioned."\
                "\nProxy Statement:"+content+"\n"\
                "\nSchema"+question_schema_string+"\n"
                
                batch_file.append(batch_row)
        return batch_file
    def split_insider_name(self,insider):
        insider = insider.lstrip().rstrip()
        name_check = insider.split(" ")
        first_name = insider
        last_name = ""
        if len(name_check) > 1:
            first_name = name_check[0]
            last_name = name_check[-1]
        first_last_name = {"first":first_name,"last":last_name, "full":insider}
        return first_last_name
    def generate_question_schema(self,insider):
        schema = {}
        ownership_requirement = "<What is the Stock Ownership Requirement for "+insider+"? If requirements are not mentioned for "+insider+", list any general requirements mentioned. Only include information about the current company and include a rationalle for the amount of stock they're required to own.>"
        compensation = "<What compensation has "+insider+" received? List all components of compensation mentioned including retainers. Only include compensation related to the current company and give a detailed breakdown of any calculations involved.>"
        accounting_experience = "<How many years of Accounting Experience does "+insider+" have at the current company? If not explictly mentioned, say so.>"
        investing_experience = "<How many years of Investing Experience does "+insider+" have at the current company? If not explicly mentioned, say so.>"
        industry_experience = "<How many years of Industry Experience does "+insider+" have at the current company? If not explicitly mentioned, estimate it based on their tenure at the current company.>"
        tenure = "<How long was "+insider+" at the current company?>"
        title = "<What is "+insider+"'s title at the current company?>"
        schema["ownership_requirement"] = ownership_requirement
        schema["compensation"] = compensation
        schema["accounting_experience"] = accounting_experience
        schema["investing_experience"] = investing_experience
        schema["industry_experience"] = industry_experience
        schema["tenure"] = tenure
        schema["title"] = title
        return schema
    def parse_CSV(self,data, header, delim):
        csv_parsed = []
        headers = []
        data = str(data)
        csv_data = data.split("\n")
        line = 0
        for row in csv_data:
            if header and line == 0:
                csv_headers_split = row.split(delim)
                for header in csv_headers_split:
                    headers.append(header)
                line += 1
            elif line > 0:
                current_row_data_split = row.split(delim)
                column_index = 0
                row_data_dict = {}
                for column_index in range(len(current_row_data_split)):
                    row_data_dict[headers[column_index]] = current_row_data_split[column_index]
                csv_parsed.append(row_data_dict)
        return csv_parsed
    def read_and_parse_CSV(self,filename, header, delim):
        csv_parsed = []
        headers = []
        with open(filename,"r") as csv_file:
            csv_data = csv_file.readline().replace("\n","").replace("\ufeff","")
            if header:
                csv_headers_split = csv_data.split(delim)
                for header in csv_headers_split:
                    headers.append(header)
                csv_data = csv_file.readline().replace("\n","")
            else:
                headers = ["symbol","insider"]
            while csv_data != '':
                current_row_data_split = csv_data.split(delim)
                column_index = 0
                row_data_dict = {}
                for column_index in range(len(current_row_data_split)):
                    row_data_dict[headers[column_index]] = current_row_data_split[column_index]
                csv_parsed.append(row_data_dict)
                csv_data = csv_file.readline().replace("\n","")
        return csv_parsed



