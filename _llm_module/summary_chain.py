from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
    PromptTemplate
)

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.output_parsers import StrOutputParser

from operator import itemgetter

from langchain.output_parsers import StructuredOutputParser, CommaSeparatedListOutputParser, PydanticOutputParser, CommaSeparatedListOutputParser
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field
from typing import List

import os

class LabelChain:
    def __init__(self):
        self.role = """ 
            Your receive transcriptions of audio messages. Your job is to label the subject
            of the message. You tag the message with multiple lables. You are both general and 
            specific. Your tags generally belong to a category, theme, or topic. 

            Messages could be about anything. Messages could be a boult multiple topics. In the 
            case of multiple topics tag with lables that fit the main topic. Ensure that a 
            general theme is tagged. All labels should have a general association with each other.
            
            It is likely that there are errors in the transcription, don't let that distract you.

            -- EXAMPLE 1 --
            Message: So I had this idea about a new app. The app will be a social media app that tracks
            users across the platform to determine their interests. Profile information will be used to
            present the user hyper-targeted ads.

            Output: technology, social media, advertising, computer science, software development,
            artificial intelligence, machine learning, data science, data analytics, data engineering

            -- EXAMPLE 2 --
            Message: I have a new idea for a business. I want to start a new business that sells a sweet
            and tangy beverage. The beverage will be made from a fruit that is grown in the tropics called
            lemon. Before starting the business I will need to create a financial model and marketing plan.

            Output: business, entrepreneurship, finance, marketing, economics, accounting, management

            FORMAT INSTRUCTIONS:
            You must follow these instructions for formating output....
        """
        self.output_parser = CommaSeparatedListOutputParser()

        self.system_prompt = PromptTemplate(
            template=self.role + "\n{format_instructions}",
            input_variables=[],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )

        self.query = "{transcript}"

        self.prompt = ChatPromptTemplate(messages=[
                    SystemMessagePromptTemplate(prompt=self.system_prompt), 
                    HumanMessagePromptTemplate.from_template(self.query)
                ])

        self.model = ChatOpenAI(model="gpt-3.5-turbo")

        self.label_chain = self.prompt | self.model | self.output_parser

    def invoke(self, input_dict):
        return self.label_chain.invoke(input_dict)

###### CLEAN UP ########
# Prompt Template
# ---------------
class CleanUpChain():
    def __init__(self):
        role = """ 
            Your receive transcriptions of audio messages. It is likely that there are
            errors in the transcription. Your job is to correct these errors. 

            You will do this by identifying the errors and correcting them. There is no 
            need to retype the entire message. You should simple output text that can 
            be used to identify the error and the correction.

            You will be provided with labels that describe the content of the message generally.
            Some labels will be more applicable than others. These labels should help you
            identify the errors by providing context.

            Acronyms and abbreviations are commonly transcribed incorrectly. The labels should 
            be very helpful in identifying these errors. If label is helpful and an acronym of 
            the raw transcription does not make sense, then use the label to correct the error.

            REMINDER: Use minimal viable text to uniquely identify the error. Punctuation, grammar,
            spelling, capitalization, and acronyms are all fair game.

            -- EXAMPLE 1 --
            Labels: shopping, produce, fruit, grocery store, supermarket, food, shopping list
            Transcription: I went to the store early and bought fruit. Except I forgot to 
            buy orangutans.

            Error: Except I forgot to buy orangutans.

            Correction: Except I forgot to buy oranges.

            -- EXAMPLE 2 --
            Labels: technology, social media, advertising, computer science, software development
            Transcription: So I had this idea about a new app. The app will be a social media app
            that tracks users across the platform to determine their interests. The app will utilize
            a new type of AI model called LOLms that can be used to interpret users posts. I will use
            one from a company called OpenAI called GBTT-4.

            Error: AI model called LOLms

            Correction: AI model called LLMs

            Error: OpenAI called GBTT-4

            Correction: OpenAI called GPT-4

            FOLLOW OUTPUT INSTRUCTIONS CAREFULLY

        """

        # Define a custom Pydantic model for error correction pairs
        class ErrorCorrectionPair(BaseModel):
            error: str = Field(description="The incorrect part of the transcription")
            correction: str = Field(description="The corrected part of the transcription")

        class ErrorCorrectionContainer(BaseModel):
            error_correction_pairs: List[ErrorCorrectionPair] = Field(description="A list of error correction pairs")

        # Define a PydanticOutputParser with the custom Pydantic model
        correction_parser = PydanticOutputParser(pydantic_object=ErrorCorrectionContainer)

        query = "Labels: {labels}\n Transcription: {transcript}"

        system_prompt = PromptTemplate(
            template=role + "\n{format_instructions}",
            input_variables=[],
            partial_variables={"format_instructions": correction_parser.get_format_instructions()}
        )

        prompt = ChatPromptTemplate(messages=[
                    SystemMessagePromptTemplate(prompt=system_prompt), 
                    HumanMessagePromptTemplate.from_template(query)
                ])


        # model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.)
        model = ChatOpenAI(model="gpt-4", temperature=0.0)

        # Update the correction_chain to include the parser
        self.chain = (
            {
            'transcript' : itemgetter('transcript'),
            'labels' : itemgetter('labels'),
            'error_correction_pairs' : prompt | model | correction_parser
            }
            | RunnableLambda(self.apply_corrections)
        )

    # Define the apply_corrections method inside the CleanUp class
    @staticmethod
    def apply_corrections(input_dict):
        # from pprint import pprint
        # pprint(input_dict)
        transcript = input_dict['transcript']
        error_correction_pairs = input_dict['error_correction_pairs'].error_correction_pairs
        for pair in error_correction_pairs:
            transcript = transcript.replace(pair.error, pair.correction)

        output_dict = input_dict
        output_dict['transcript'] = transcript

        print("Fixed transcription: ", transcript)
        return output_dict
        
    def invoke(self, input_dict):
        return self.chain.invoke(input_dict)



class SummaryChain:
    def __init__(self):
        self.role = """ 
            You have mastery of the English language. You specialize in helping writers and speakers better
            communicate there ideas. You are a professional editor. You are a master of grammar and spelling.
            
            Your receive transcriptions of audio messages. You will be provided with labels that describe the
            audio message. These labels should make sense in the context of the message. 
            
            Your job is to summarize the transcription. You should summarize the message in context to one
            or more of the labels. The summary should be contain all important details of the original message.
            However, the summary should be concise. Please keep the summary to be the same length or shorter
            than the original message.

            Keep in mind that the transcription may not be concise or struggle to properly articulate idea. This
            is the crux of you task. Interpret the messages intent without introducing new ideas. Interpret and 
            concolidate.

            FOR THE SAKE OF THE USER, PLEASE ATTEMPT TO MAINTAIN SOME OF THE USERS TONE AND STYLE. KEEP IT IN THE VOICE
            OF THE USER. IF FIRST PERSON, KEEP IT FIRST PERSON. IF FIRST PERSON, KEEP IT FIRST PERSON.
        """

        self.query = "Labels: {labels}\n Transcription: {transcript}"

        self.prompt = ChatPromptTemplate(messages=[
                    SystemMessagePromptTemplate.from_template(self.role),
                    HumanMessagePromptTemplate.from_template(self.query)
                ])

        self.model = ChatOpenAI(
            model="gpt-4",
            streaming=True, 
            callbacks=[StreamingStdOutCallbackHandler()]
        )

        self.chain = self.prompt | self.model | StrOutputParser()

    def invoke(self, input_dict):
        return self.chain.invoke(input_dict)
    
