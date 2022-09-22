print ("hello karthik this is python")
print ("welcome to karthik learnings")
print ("new change made")
print ("started new print")
# 4.1 - What is a String?
# Solutions to review exercies


# Exercise 1
print('There are "double quotes" in this string.')


# Exercise 2
print("This string's got an apostrophe.")


# Exercise 3
print(
    """This string was written on multiple lines,
      and it displays across multiple lines"""
)


# Exercise 4
print(
    "This one-line string was written out \
      using multiple lines"
)

# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

name: Java CI

on: [push, pull_request]

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macOS-latest]
      fail-fast: false

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-java@v2
        with:
          java-version: 8
          distribution: 'temurin'
          cache: 'maven'

      - name: Build with Maven
        run: mvn verify -e -B -V -DdistributionFileName=apache-maven

      - name: Upload built Maven
        uses: actions/upload-artifact@v2
        if: ${{ matrix.os == 'ubuntu-latest' }}
        with:
          name: built-maven
          path: apache-maven/target/

  integration-test:
    needs: build
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macOS-latest]
        java: [8, 11, 17]

      fail-fast: false
    runs-on: ${{ matrix.os }}

    steps:
      - name: Collect environment context variables
        shell: bash
        env:
          PR_HEAD_LABEL: ${{ github.event.pull_request.head.label }}
        run: |
          set +e
          repo=maven-integration-testing
          target_branch=master
          target_user=apache
          if [ "$GITHUB_EVENT_NAME" == "pull_request" ]; then
            user=${PR_HEAD_LABEL%:*}
            branch=${PR_HEAD_LABEL#*:}
          else
            user=${GITHUB_REPOSITORY%/*}
            branch=${GITHUB_REF#refs/heads/}
          fi
          if [ $branch != "master" ]; then
            git ls-remote https://github.com/$user/$repo.git | grep "refs/heads/${branch}$" > /dev/null
            if [ $? -eq 0 ]; then
              echo "Found a branch \"$branch\" in fork \"$user/$repo\", configuring this for the integration tests to be run against."
              target_branch=$branch
              target_user=$user
            else
              echo "Could not find fork \"$user/$repo\" or a branch \"$branch\" in this fork. Falling back to \"$target_branch\" in \"$target_user/$repo\"."
            fi
          else
            echo "Integration tests will run against $target_user/$repo for master builds."
          fi
          echo "REPO_BRANCH=$target_branch" >> $GITHUB_ENV
          echo "REPO_USER=$target_user" >> $GITHUB_ENV

      - name: Checkout maven-integration-testing
        uses: actions/checkout@v2
        with:
          repository: ${{ env.REPO_USER }}/maven-integration-testing
          path: maven-integration-testing/
          ref: ${{ env.REPO_BRANCH }}

      - name: Set up cache for ~/.m2/repository
        uses: actions/cache@v2
        with:
          path: ~/.m2/repository
          key: it-m2-repo-${{ matrix.os }}-${{ hashFiles('maven-integration-testing/**/pom.xml') }}
          restore-keys: |
            it-m2-repo-${{ matrix.os }}-

      - name: Download built Maven
        uses: actions/download-artifact@v2
        with:
          name: built-maven
          path: built-maven/

      - name: Set up JDK
        uses: actions/setup-java@v2
        with:
          java-version: ${{ matrix.java }}
          distribution: 'temurin'
          cache: 'maven'

      - name: Running integration tests
        shell: bash
        run: mvn install -e -B -V -Prun-its,embedded -Dmaven.repo.local="$HOME/.m2/repository" -DmavenDistro="$GITHUB_WORKSPACE/built-maven/apache-maven-bin.zip" -f maven-integration-testing/pom.xml
